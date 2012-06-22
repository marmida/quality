'''
Calculate C.R.A.P. scores for Python modules.

For background on C.R.A.P., see http://www.artima.com/weblogs/viewpost.jsp?thread=215899
'''

import quality.complexity


import ast
import os.path
import warnings
import xml.etree.ElementTree

def gen_class_elems(doc):
    '''
    yield 'class' elements from a coverage.xml document
    '''
    for package_elem in doc.getroot()[0]:
        for class_elem in package_elem[0]:
            yield class_elem

def find_class_elem(doc, source_path, coverage_file):
    '''
    Return the <class> element inside the XML document `doc` that contains the 
    coverage data for the file `source_path`.  If not found, return None.

    The 'coverage' command provides the 'filename' attribute to 'class' 
    elements, but it can contain a relative path, depending on the invocation of
    the 'coverage' command.

    Because of this, we need to line up three paths: (1) the path to coverage.xml,
    (2) paths to source files referenced by coverage.xml, and (3) the path to 
    the source file.  We assume that coverage.xml paths are relative to the 
    directory containing coverage.xml.

    Args:
    * `doc` - etree-style document representing coverage.xml
    * `source_path` - the path to the python module being scored
    * `coverage_file` - path to, or file object representing, the coverage.xml document
    '''
    abs_source_path = os.path.abspath(source_path)
    # ensure coverage_file is a path
    if isinstance(coverage_file, file):
        # allow AttributeErrors if coverage_file is a file that doesn't support names
        coverage_file = coverage_file.name
    coverage_dir = os.path.dirname(coverage_file)

    for class_elem in gen_class_elems(doc):
        if os.path.abspath(os.path.join(coverage_dir, class_elem.get('filename'))) == abs_source_path:
            break
    else:
        return None
    return class_elem

def extract_line_nums(doc, source_path, coverage_file):
    '''
    Extract a two sets of line numbers from coverage.xml: "hit" and "missed" lines.
    
    * `doc` - etree-style document representing coverage.xml
    * `source_path` - the path to the python module being scored
    * `coverage_file` - path to, or file object representing, the coverage.xml document
    '''
    class_elem = find_class_elem(doc, source_path, coverage_file)
    if class_elem == None:
        warnings.warn('Could not find coverage data for source file: %s; proceeding under the assumption that this code is uncovered'
            % source_path)
        # we'll assume every line in the file is a statement line; this is ok, 
        # because this just gets intersected with the ast version anyway
        return frozenset(), frozenset(range(sum(1 for l in open(source_path))))
    
    hit_lines = set()
    missed_lines = set()
    for line_elem in class_elem[1]:
        (hit_lines if line_elem.get('hits') == '1' else missed_lines).add(int(line_elem.get('number')))

    return hit_lines, missed_lines

class CrapJudge(object):
    '''
    Calculates C.R.A.P. scores for Contestants.

    Implementation note: this is a bit wonky as a class.  It's done so to
    avoid having to re-parse the coverage.xml and re-calculate hit and 
    missed lines for each contestant.

    It might be better to give each judge a separate entry point for:
    (1) each source file
    (2) each Contestant
    (3) its own initialization / receiving instance options from command-line 
        opts?

    But this begs the question of how command-line options are handed to
    Judge instances; are there per-source, per-Contestant, and per-instance
    options?  Our only extant option, `coverage_file`, would be per-source.

    Attributes:

    * coverage - dict mapping filenames to sets of line numbers, (hit_lines, missed_lines)
    * unified - dict mapping filenames to sets of all line numbers in coverage.xml: hit_lines | missed_lines
    '''
    _quality_judge_name = 'crap'

    def __init__(self):
        self.coverage = {}
        self.unified = {} # todo: turn this into a property that dynamically combines the hit and miss sets on the fly
        
    def coverage_ratio(self, contestant):
        '''
        Find the proportion of the line numbers for `contestant` that were 
        reported covered in coverage.xml.

        Returns a float.
        '''
        fixed_lines = self.align_linenums(contestant)

        if len(fixed_lines) == 0:
            # if a def has no lines, we'll call it 100% covered.
            return 1.0

        return float(len(fixed_lines & self.coverage[contestant.src_file][0])) / len(fixed_lines)

    def align_linenums(self, contestant):
        '''
        Return a set of linenums in `contestant`, adjusted so they match the 
        line numbers reported by coverage.xml.

        We do this by filtering out lines that don't appear in the union of
        hit and missed lines from coverage.xml.  This assumes that every 
        line number in the contestant is also in coverage.xml.

        Background:
        coverage.xml is produced by coverage.py, which gets line numbers 
        of executed code from cPython.  This differs from the line numbers
        generated by the ast module, as described here:
        https://bitbucket.org/ned/coveragepy/issue/180/last-of-certain-multi-line-statements-is
        '''
        return contestant.linenums & self.unified[contestant.src_file]

    def __call__(self, contestant, coverage_file=None):
        '''
        Return the C.R.A.P. score for a Contestant.

        Arguments:
        * `contestant` - a Contestant
        * `coverage_file` - path to, or file object representing, the coverage.xml document
        '''
        complexity = quality.complexity.complexity(contestant.node)
        
        if contestant.src_file not in self.coverage:
            # we haven't yet cached coverage info for this module; do so now
            coverage_doc = xml.etree.ElementTree.parse(coverage_file)
            hit, miss = extract_line_nums(coverage_doc, contestant.src_file, coverage_file)
            self.coverage[contestant.src_file] = (hit, miss)
            self.unified[contestant.src_file] = hit | miss
        cov_ratio = self.coverage_ratio(contestant)

        return (complexity ** 2) * (1 - cov_ratio) + complexity
