'''
Code quality analysis for Python.
'''

# general module todo: what about lambdas?

import ast

# ###
# Our concept of "qualified name" : http://www.python.org/dev/peps/pep-3155/
# until PEP-3155 is ubiquitous, we do that work ourselves in annotate_qualname

def annotate_linenums(node):
    '''
    post-order traversal of `node`, adding to each node an attribute: 'descendant_lines'

    This attribute gets added only if the node is a ClassDef, FunctionDef, or Module,
    and contains a set of line numbers of descendant nodes not contained by an 
    intervening ClassDef or FunctionDef.
    '''
    descendant_lines = set()
    children = iter(node.body) if node.__class__.__name__ in ['ClassDef', 'FunctionDef'] else ast.iter_child_nodes(node)

    # exclude docstrings from line numbers
    first_child = True
    for i in children:
        if first_child and i.__class__.__name__ == 'Expr' and i.value.__class__.__name__ == 'Str':
            # this is a docstring
            first_child = False
            continue
        first_child = False
        descendant_lines.update(annotate_linenums(i))

    # if this node is a module, class or function def, store the collected line numbers in it
    if node.__class__.__name__ in ['Module', 'ClassDef', 'FunctionDef']:
        node.descendant_lines = descendant_lines
        return frozenset()

    # otherwise, bubble up the collected lines
    if hasattr(node, 'lineno'):
        descendant_lines.add(node.lineno)
    return descendant_lines

def annotate_qualnames(node, parents=None):
    '''
    Append 'qualname' attributes to FunctionDef and ClassDef nodes

    todo: handle multiple definitions of the same name in the same scope, e.g.:

        def outer():
            def inner():
                pass
            def inner():
                pass
    '''
    if not parents:
        parents = []
    
    if node.__class__.__name__ in ['ClassDef', 'FunctionDef']:
        # todo: copying this list is inefficient; fix this.
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

def find_contestants(node, src_path):
    '''
    Return a list of Contestants representing qualifying nodes:
    Modules, ClassDefs, and FunctionDefs

    - `node` - ast node
    - `src_path` - filename of the original source
    '''
    ret = []

    if node.__class__.__name__ in ['Module', 'ClassDef', 'FunctionDef']:
        ret.append(Contestant(node, src_path))
        
    for child in ast.iter_child_nodes(node):
        ret += find_contestants(child, src_path)

    return ret

class Contestant(object):
    '''
    An item that can have a quality score:
    - a module
    - a function
    - a class
    - a class method

    Basically, anything that has a scope.  Lambdas currently aren't included, but probably should be.

    Attributes:
    * node - AST node that represents this item in the source
    * name - qualified name of the object
    * linenums - set of line numbers not contained under a child Contestant
    * scorecards - scores from each indivdual judge
    * final_score - combined score from all judges
    * src_file - path to the source file defining this Contestant
    '''
    def __init__(self, node, src_file):
        self.node = node
        self.name = getattr(node, 'qualname', '<module>')
        self.linenums = node.descendant_lines
        self.scores = None
        self.final_score = None
        self.src_file = src_file

def extract_judge_kwargs(judge_name, kwargs):
    '''
    filter a dict, returning only keys that start with `judge_name`, followed by a colon.

    The result contains keys with this prefix stripped.
    '''
    prefix = judge_name + ':'

    filtered = dict((k[len(prefix):], v) for k, v in kwargs.iteritems() if k.startswith(prefix))
    return filtered

def run_contest(src_paths, options, formula, recruited_judges):
    '''
    Discover contestants inside each of the source files, and 
    record the results of each judge applied to them.  Finally,
    calculate the final, combined score for each contestant, using the 
    provided formula.

    Returns a dictionary mapping source filenames to a list of 
    contestants contained in that file.  The contestants are unordered.
    '''
    results = {}

    for src_path in src_paths:
        # create Contestants from the source
        src_tree = ast.parse(open(src_path).read(), filename=src_path)
        
        # add linenums and qualnames to nodes
        annotate_qualnames(src_tree)
        annotate_linenums(src_tree)

        # build a list of contestants
        contestants = find_contestants(src_tree, src_path)

        for contestant in contestants:
            contestant.scores = dict((judge._quality_judge_name, judge(contestant, **extract_judge_kwargs(judge._quality_judge_name, options))) for judge in recruited_judges)
            context = contestant.scores.copy()
            # import pdb; pdb.set_trace()
            context['__builtins__'] = __builtins__
            contestant.final_score = eval(formula, context)

        results[src_path] = contestants

    return results

def load_judges():
    '''
    Currently, returns a canned set of judges.

    Eventually this should be expanded to allow for dynamic loading and discovery.
    '''
    import quality.crap
    import quality.indentation
    
    return [
        quality.crap.CrapJudge().judge_crap, 
        quality.indentation.TabnannyJudge().judge_tabnanny,
    ]

