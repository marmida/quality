'''
Command-line interface to quality calculation
'''

import quality.core
import quality.report


import optparse
import os
import os.path
import re
import StringIO
import token
import tokenize

def default_quality_formula():
    'the stock formula, used with simple_parse_args'
    return 'crap'

class FixedHelpFormatter(optparse.IndentedHelpFormatter):
    'Don\'t re-wrap description text'
    def format_description(self, description):
        return description

def find_source_files(source_dir, exclude=None, include=None):
    '''
    Return a list of paths to Python source files in `source_dir`

    If provided, `exclude` is a list of regexes; candidates are 
    excluded if they match any of these patterns.

    If provided, `include` is a list of regexes; candidates are
    included only if they match one of these patterns.

    If both `exclude` and `include` are provided, raise ValueError.

    If `source_dir` is not a directory, only raise an error if it
    doesn't look like a Python source file.
    '''
    if os.path.isfile(source_dir) and source_dir.endswith('.py'):
        # source_dir is a single file
        return [source_dir]

    if not os.path.isdir(source_dir) and not source_dir.endswith('.py'):
        raise ValueError('Is neither a directory, nor a Python source file: %s' % source_dir)

    if exclude and include:
        raise ValueError('cannot handle both exclude and include patterns')

    # make a function to encapsulate any filtering
    # there's probably a clever way to do exclude and include using generators,
    # but I can't think of a way to guarantee it short-circuits
    if exclude:
        def filter_fn(x):
            for regex in exclude:
                if regex.search(x):
                    return False
            return True
    elif include:
        def filter_fn(x):
            for regex in include:
                if regex.search(x):
                    return True
            return False
    else:
        filter_fn = lambda x: True

    source_files = []
    for dirpath, dirnames, filenames in os.walk(source_dir):
        source_files += [os.path.join(dirpath, filename) for filename in 
            filenames if filename.endswith('.py') and os.path.isfile(os.path.join(dirpath, filename))
            and filter_fn(os.path.join(dirpath, filename))]

    return source_files

def simple_parse_args(judge_names):
    'parse command-line args while making a lot of assumptions; quick-start mode'
    parser = optparse.OptionParser(
        description='''Examine a set of Python modules and calculate the code quality of each.

Arguments:
    * source_dir: path to a directory, under which to score all contained modules
    * coverage_path: path to the coverage.xml with data for the above modules
''',
        usage='%prog [options] coverage_path source_dir',
        formatter=FixedHelpFormatter(),
    )
    parser.add_option('-f', '--formula', action='store', default=default_quality_formula(), 
        help='Formula for calculating final scores')
    parser.add_option('-x', '--exclude', action='append',
        help='Exclude source files matching this pattern; can be specified multiple times')
    parser.add_option('-i', '--include', action='append',
        help='Include only source files matching this pattern; can be specified multiple times')
    
    opts, args = parser.parse_args()

    targets = []
    if len(args) != 2:
        parser.error("Incorrect number of arguments")
    
    coverage_file, source_dir = args

    # validate args
    if not os.path.isfile(coverage_file):
        parser.error('Invalid coverage file argument: %s' % coverage_file)
    source_options = {'crap:coverage_file': coverage_file}

    # validate formula
    judges = [toktext for toktype, toktext, (_, _), (_, _), _ in tokenize.generate_tokens(StringIO.StringIO(opts.formula).readline)
        if toktype == token.NAME and toktext in judge_names]
    if judges == []:
        parser.error('Provided formula doesn\'t include any known metric names: %s' % opts.formula)

    # validate include/exclude
    if opts.exclude and opts.include:
        parser.error('Cannot combine both \'exclude\' and \'include\' options')
    try:
        if opts.include:
            opts.include = [re.compile(i) for i in opts.include]
        if opts.exclude:
            opts.exclude = [re.compile(i) for i in opts.exclude]
    except re.error, exc:
        parser.error('Error parsing regular expression: %s' % exc.args[0])

    # find Python source files
    source_files = find_source_files(source_dir, exclude=opts.exclude, include=opts.include)
    if source_files == []:
        parser.error('Did not find any files ending in .py within %s' % source_dir)

    # compile the formula for final scoring
    opts.formula = compile(opts.formula, filename='<formula>', mode='eval')

    # todo: add some validations to formula?
    # this might not be possible without running it

    return (source_files, source_options), opts, judges



def main():
    judges = quality.core.load_judges()

    (source_files, source_options), opts, recruited_judge_names = simple_parse_args([judge._quality_judge_name for judge in judges])
    recruited_judges = [judge for judge in judges if judge._quality_judge_name in recruited_judge_names]

    results = quality.core.run_contest(source_files, source_options, opts.formula, recruited_judges)

    # todo: allow for different types of reporters, and to get configuration options to them

    reporters = [quality.report.print_report]
    for reporter in reporters:
        reporter(results)