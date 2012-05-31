import quality.crap

import ast
from nose.tools import *

def test_calc_coverage_ratio():
    assert_equal(0.5, quality.crap.calc_coverage_ratio([5, 6, 15, 16], set([15, 16])))
    assert_equal(0.0, quality.crap.calc_coverage_ratio([4, 5, 6], set([1, 2, 3])))
    # checking for divide-by-zero
    assert_equal(1.0, quality.crap.calc_coverage_ratio([], set([])))


def test_CCAnnotator():
    tree = ast.parse('''
def function_a():
    pass

def function_b():
    if True == False:
        pass

def function_c():
    for i in range(3):
        pass
    while True:
        pass
    if True and True and True or True:
        pass
        ''')
    quality.crap.CCAnnotator().visit(tree)
    assert_equal(0, tree.complexity) # shouldn't this be 1?  There is one path through a module with no code in it.
    assert_equal(1, tree.body[0].complexity)
    assert_equal(2, tree.body[1].complexity)
    assert_equal(6, tree.body[2].complexity)

    # test nesting
    tree = ast.parse('''
def outer():
    if True == False:
        def inner():
            pass
''')
    quality.crap.CCAnnotator().visit(tree)
    assert_equal(0, tree.complexity)
    assert_equal(2, tree.body[0].complexity)
    assert_equal(1, tree.body[0].body[0].body[0].complexity)

    # test module- and class-level complexity
    tree = ast.parse('''
if True == False:
    pass

class Hello(object):
    if True == False:
        pass
    def method_a(self):
        pass
''')
    quality.crap.CCAnnotator().visit(tree)
    assert_equal(1, tree.complexity)
    assert_equal(2, tree.body[1].complexity)
    assert_equal(1, tree.body[1].body[1].complexity)