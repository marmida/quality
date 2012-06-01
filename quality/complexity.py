'''
Services for calculating cyclomatic complexity against AST trees.

Inspired by David Stanek's pygenie/cc.py.
'''

import ast

# a list of things that bump up complexity scores
_CC_NODE_TYPES = [
    'FunctionDef', # is this correct? Does this really add a path through the code?
    'ClassDef', # and this as well?
    'For',
    'While',
    'If',
    'With',
    'IfExp',
    'ListComp', # cc.py includes lists, but of the other comps; was it just too old?
    'SetComp',
    'DictComp',
    'BoolOp',
]


def complexity(node):
    '''
    Descend to child nodes and sum their complexity.  Avoids descending into other 
    "contestant" type nodes, in our contest analogy: Modules, FunctionDefs, and ClassDefs.
    '''
    child_complexity = sum(complexity(child) for child in ast.iter_child_nodes(node)
        if child.__class__.__name__ not in ['Module', 'FunctionDef', 'ClassDef'])

    cur_complexity = 1 if node.__class__.__name__ in _CC_NODE_TYPES else 0

    return cur_complexity + child_complexity