'''
Code quality analysis for Python.

Currently, this means "C.R.A.P. metric calculation for Python."  For background
on C.R.A.P., see http://www.artima.com/weblogs/viewpost.jsp?thread=215899
'''

# general module todo: what about lambdas?

import ast
import xml.etree.ElementTree
import os.path

# ###
# About annotate_linenums:
# 
# see also: http://www.python.org/dev/peps/pep-3155/
# until PEP-3155 is ubiquitous, we do that work ourselves in annotate_qualname

# Notes about our line number strategy: 
# We need produce line numbers that match up with coverage.py's analysis
# coverage.py produces statement line numbers via the 'xml' command; it 
# does not, for instance, include the 'else:' lines of if statements, since
# they aren't statements themselves.
# This is different than the 'annotate' command of coverage; it has special
# logic for cases like 'else:', and includes them.

def annotate_linenums(node):
    '''
    post-order traversal of 'node', adding to each node an attribute: 'descendant_lines'

    This attribute gets added only if the node is a ClassDef, FunctionDef, or Module,
    and contains a sorted list of the line numbers of descendant nodes not contained by 
    an intervening ClassDef or FunctionDef.

    todo: don't bother changing results back to a list; it's just going to get converted back to a set
    '''
    descendant_lines = set()
    children = iter(node.body) if node.__class__.__name__ in ['ClassDef', 'FunctionDef'] else ast.iter_child_nodes(node)

    first_child = True
    for i in children:
        if first_child and i.__class__.__name__ == 'Expr' and i.value.__class__.__name__ == 'Str':
            # this is a docstring
            first_child = False
            continue
        descendant_lines.update(annotate_linenums(i))

    # if this node is a module, class or function def, store the collected line numbers in it
    if node.__class__.__name__ in ['Module', 'ClassDef', 'FunctionDef']:
        node.descendant_lines = sorted(list(descendant_lines))
        return frozenset()

    # otherwise, bubble up the collected lines
    if hasattr(node, 'lineno'):
        descendant_lines.add(node.lineno)
    return descendant_lines

def annotate_qualnames(node, parents=[]):
    '''
    Append 'qualname' attributes to FunctionDef and ClassDef nodes

    todo: handle multiple definitions of the same name in the same scope, e.g.:

        def outer():
            def inner():
                pass
            def inner():
                pass
    '''
    
    if node.__class__.__name__ in ['ClassDef', 'FunctionDef']:
        new_parents = parents[:]
        new_parents.append(node.name)
        node.qualname = '.'.join(new_parents)
    else:
        if node.__class__.__name__ == 'Module':
            # todo: how do we want to handle module names?  If we use the name of the module, (a) that will get prepended
            # to all child nodes, (b) that implies a path from Python code, which is dependent on a particular sys.path.
            node.qualname = '<module>'
        new_parents = parents

    for i in ast.iter_child_nodes(node):
        annotate_qualnames(i, new_parents)

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
    # listed in order of the 'ast' module docs' grammar listing
    visit_For = visit_While = visit_If = visit_With \
        = visit_IfExp = visit_ListComp = visit_SetComp = visit_DictComp \
        = _visit_control

    # and, or nodes
    def visit_BoolOp(self, node):
        '''
        and/or: complexity +1
        '''
        return 1

def find_defs(node, ls):
    '''
    Populate ls with a list of nodes from the ast tree that are definitions: 
    modules, functions, and classes.

    todo: refactor this extra-ugly function; it builds a list as a side-effect
    '''
    if node.__class__.__name__ in ['Module', 'ClassDef', 'FunctionDef']:
        ls.append(node)

    for child in ast.iter_child_nodes(node):
        find_defs(child, ls)

def gen_class_elems(doc):
    '''
    yield 'class' elements from a coverage.xml document
    '''
    for package_elem in doc.getroot()[0]:
        for class_elem in package_elem[0]:
            yield class_elem

def extract_hit_lines(doc, source_path):
    '''
    Extract from the etree-style doc a set of lines that are covered by unit tests.
    'source_path' is the path to the file under test.
    '''
    for class_elem in gen_class_elems(doc):
        if class_elem.get('filename') == source_path:
            break
    else:
        raise ValueError('couldn\'t find coverage data for source file "%s" in coverage.xml document' % source_path)

    hit_lines = set()
    for line_elem in class_elem[1]:
        if line_elem.get('hits') == '1':
            hit_lines.add(int(line_elem.get('number')))

    return hit_lines

def calc_coverage_ratio(def_lines, hit_lines):
    '''
    Compare the lines inside the definition, 'def_lines', against the lines reported
    hit by the unit tests, 'hit_lines', and return the prortion of coverage.
    '''
    if len(def_lines) == 0:
        # if a def has no lines, we'll call it 100% covered.
        return 1.0
    return float(len(frozenset(def_lines) & hit_lines)) / len(def_lines)
    

def quality(coverage_xml_path, src_path):
    # digest coverage.xml
    coverage_doc = xml.etree.ElementTree.parse(coverage_xml_path)
    hit_lines = extract_hit_lines(coverage_doc, src_path)

    # annotate the ast of the source
    # todo: refactor or redesign; we're using the AST tree to store our data, and that means
    # passing around the same args over and over, C-style.
    src_tree = ast.parse(open(src_path).read(), filename=src_path)
    annotate_qualnames(src_tree)
    annotate_linenums(src_tree)
    CCAnnotator().visit(src_tree)

    defs = []
    find_defs(src_tree, defs)
    
    ret = []
    for def_node in defs:
        cov_ratio = calc_coverage_ratio(def_node.descendant_lines, hit_lines)

        # for each definition, calculate quality
        quality = (def_node.complexity ** 2) * (1 - cov_ratio) + def_node.complexity
        ret.append((def_node.qualname, quality))

    return ret
