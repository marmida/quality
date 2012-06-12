'''
Command-line interface to quality calculation

example invocations:

quality.py crap 
'''

import quality.quality
import quality.report


import optparse
import os
import os.path
import StringIO
import token
import tokenize

def default_quality_formula():
    'the stock formula, used with simple_parse_args'
    return 'crap'

def simple_parse_args(judge_names):
    'parse command-line args while making a lot of assumptions; quick-start mode'
    parser = optparse.OptionParser(
        description='''Examine a set of Python modules, contained in source dir, and calculate the code quality of each.

Arguments:
    * source_dir: path to a directory, under which to score all Python modules
    * coverage_path: path to the coverage.xml including the above modules''',
        usage='%prog [options] coverage_path source_dir',
    )
    parser.add_option('-f', '--formula', action='store', default=default_quality_formula(), 
        help='Formula for calculating final scores')
    
    opts, args = parser.parse_args()

    targets = []
    if len(args) != 2
        parser.error("Incorrect number of arguments")
    
    coverage_file, source_dir = args

    # validate args and scan source_dir for .py files
    if not os.path.isfile(coverage_file):
        parser.error('Invalid coverage file argument: %s' % coverage_file)

    source_files = []
    for dirpath, dirnames, filenames in os.walk(source_dir):
        source_files += [os.path.join(dirpath, filename) for filename in 
            filenames if filename.endswith('.py') and os.path.isfile(os.path.join(dirpath, filename))]

    if source_files == []:
        parser.error('Did not find any files ending in .py within %s' % source_dir)

    options = {'crap:coverage_file': coverage_file}

    # validate formula
    judges = [toktext for toktype, toktext, (_, _), (_, _), _ in tokenize.generate_tokens(StringIO.StringIO(opts.formula).readline)
        if toktype == token.NAME and toktext in judge_names]
    if judges == []:
        parser.error('Provided formula doesn\'t include any known metric names: %s' % opts.formula)

    # compile the formula for final scoring
    formula = compile(opts.formula)

    # todo: add some validations to formula?
    # this might not be possible without running it

    return (source_files, options), formula, judges



def main():
    judges = quality.load_judges()

    (source_files, options), formula, recruited_judge_names = simple_parse_args([judge.name for judge in judges])
    recruited_judges = [judge for judge in judges if judge.name in recruited_judge_names]

    results = quality.run_contest(source_files, options, formula, recruited_judges)

    # todo: allow for different types of reporters, and to get configuration options to them

    reporters = [quality.report.print_report]
    for reporter in reporters:
        reporter(results)