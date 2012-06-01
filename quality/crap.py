'''
Calculate C.R.A.P. scores for Python modules.

For background on C.R.A.P., see http://www.artima.com/weblogs/viewpost.jsp?thread=215899
'''

import ast
import quality.dec

def gen_class_elems(doc):
    '''
    yield 'class' elements from a coverage.xml document
    '''
    for package_elem in doc.getroot()[0]:
        for class_elem in package_elem[0]:
            yield class_elem

def extract_line_nums(doc, source_path):
    '''
    Extract a two sets of line numbers from coverage.xml: "hit" and "missed" lines.
    
    `doc` - etree-style document representing coverage.xml
    `source_path` - the path to the file under test
    '''
    for class_elem in gen_class_elems(doc):
        if class_elem.get('filename') == source_path:
            break
    else:
        raise ValueError('couldn\'t find coverage data for source file "%s" in coverage.xml document' % source_path)

    hit_lines = set()
    missed_lines = set()
    for line_elem in class_elem[1]:
        (hit_lines if line_elem.get('hits') == '1' else missed_lines).add(int(line_elem.get('number')))

    return hit_lines, missed_lines



def fix_line_nums(node, lines):
    '''
    adjust line numbers to fix coverage.xml's idea of lines
    '''
    pass

def calc_coverage_ratio(def_lines, hit_lines):
    '''
    Compare the lines inside the definition, `def_lines`, against the lines reported
    hit by the unit tests, `hit_lines`, and return the prortion of coverage.
    '''
    if len(def_lines) == 0:
        # if a def has no lines, we'll call it 100% covered.
        return 1.0
    return float(len(frozenset(def_lines) & hit_lines)) / len(def_lines)

@quality.dec.judge('crap')
def judge_crap(contestant, coverage_file=None):
    # todo: this is really suboptimal; we're re-parsing coverage.xml and 
    # re-calculating hit and miss lines for each contestant in each file
    # instead: allow each judge a chance to inspect each module before getting
    # to each contestant?

    # digest coverage.xml
    coverage_doc = xml.etree.ElementTree.parse(coverage_file)
    hit_lines, missed_lines = extract_line_nums(coverage_doc, src_path)

    complexity = quality.complexity.visit(contestant.node)

    # reconcile line number differences between cPython and the ast module
    fix_line_nums(src_tree, hit_lines)
    fix_line_nums(src_tree, missed_lines)

    cov_ratio = calc_coverage_ratio(contestant.linenums, hit_lines)
    return (complexity ** 2) * (1 - cov_ratio) + complexity


class CCAnnotator(object):
    '''
    Almost like ast.NodeVisitor, except that I've separated the traversal/dispatching
    from the optional visiting logic; I didn't like how the other one worked.

    Heavily borrowed from David Stanek's pygenie/cc.py.

    todo: refactor; CCAnnotator isn't really a class, just a namespace for functions
    '''
    def visit(self, node):
        '''
        Descend to child nodes and sum their complexity.  Always visits all child nodes, 
        regardless of whether or not there's a visit_{NodeType} function defined.
        '''
        child_complexity = sum(self.visit(child) for child in ast.iter_child_nodes(node))

        # is there a specialized dispatch function to handle this node?
        # if not, assume the complexity of this node is 0
        visitor = getattr(self, ('visit_%s' % node.__class__.__name__), lambda x: 0)

        cur_complexity = visitor(node)

        if node.__class__.__name__ in ['Module', 'FunctionDef', 'ClassDef']:
            node.complexity = cur_complexity + child_complexity
            return 0

        return cur_complexity + child_complexity

    # class, function nodes
    def visit_FunctionDef(self, node):
        '''
        functions and classes: begin a new path of execution, so they have a complexity of 1
        '''
        return 1

    visit_ClassDef = visit_FunctionDef

    # if, for, while, with, generators, comprehensions
    def _visit_control(self, node):
        '''
        Control flow structures and comprehensions all add 1 complexity.

        todo: review cc theory and make sure comprehensions really should increase complexity
        todo: maybe 'If' should be +1 for the presence of an 'orelse'?
        '''
        return 1
    # listed in order of the 'ast' module docs' grammar listing: http://docs.python.org/library/ast.html
    visit_For = visit_While = visit_If = visit_With \
        = visit_IfExp = visit_ListComp = visit_SetComp = visit_DictComp \
        = _visit_control

    # and, or nodes
    def visit_BoolOp(self, node):
        '''
        and/or: complexity +1
        '''
        return 1