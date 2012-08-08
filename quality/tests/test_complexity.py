from __future__ import absolute_import

import quality.complexity
import quality.tests.compat # must come before import nose.tools

import ast
from nose.tools import *

def test_complexity():
    # ending the following source with an empty line causes py2.6's ast to raise SyntaxError
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
        pass''')
    assert_equal(0, quality.complexity.complexity(tree))
    assert_equal(1, quality.complexity.complexity(tree.body[0]))
    assert_equal(2, quality.complexity.complexity(tree.body[1]))
    assert_equal(6, quality.complexity.complexity(tree.body[2]))

    # test nesting
    tree = ast.parse('''
def outer():
    if True == False:
        def inner():
            pass
''')
    assert_equal(0, quality.complexity.complexity(tree))
    assert_equal(2, quality.complexity.complexity(tree.body[0]))
    assert_equal(1, quality.complexity.complexity(tree.body[0].body[0].body[0]))

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
    assert_equal(1, quality.complexity.complexity(tree))
    assert_equal(2, quality.complexity.complexity(tree.body[1]))
    assert_equal(1, quality.complexity.complexity(tree.body[1].body[1]))