import quality.core
import quality.crap

import ast
import mock
from nose.tools import *
import os.path
import sys
import unittest
import xml.etree.ElementTree

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

def test_annotate_linenums_basics():
    tree = ast.parse('''def dosomething():
    pass

def dosomethingelse():
    print 'it did something!'

if True:
    print 'hi there'
''')
    quality.core.annotate_linenums(tree)
    assert_equal(set([7, 8]), tree.descendant_lines)
    assert_equal(set([2]), tree.body[0].descendant_lines)
    assert_equal(set([5]), tree.body[1].descendant_lines)

def test_annotate_linenums_nesting():
    tree = ast.parse(''' # line 1
def dosomething():
    pass
    class Hello(object):
        CONSTANT = 'hi'
        def dosomething(self):
            if true:
                def another_something(self):
                    pass
            else:
                def another_something(self):
                    pass

            return another_something
        dosomethingelse = dosomething
''')
    quality.core.annotate_linenums(tree)
    assert_equal(set(), tree.descendant_lines)
    assert_equal(set([3]), tree.body[0].descendant_lines)
    assert_equal(set([5, 15]), tree.body[0].body[1].descendant_lines)
    # line 10 isn't part of the next assertion, because it's not a statement
    assert_equal(set([7, 14]), tree.body[0].body[1].body[1].descendant_lines)

def test_annotate_linenums_docstrings():
    tree = ast.parse('''\
'module docstring'
pass

def dosomething():
    \'\'\'
    multi-line function docstring
    \'\'\'
    pass

def not_a_docstring():
    pass
    'surprise!'
''')
    quality.core.annotate_linenums(tree)
    assert_equal(set([2]), tree.descendant_lines)
    assert_equal(set([8]), tree.body[2].descendant_lines)
    assert_equal(set([11, 12]), tree.body[3].descendant_lines)

def test_annotate_linenums_multiline():
    '''
    annotate_linenums: multi-line statements should include both lines
    '''
    tree = ast.parse('''a = \\
3''')
    quality.core.annotate_linenums(tree)
    assert_equal(set([1, 2]), tree.descendant_lines)

def test_annotate_qualnames():
    tree = ast.parse('''
def function_a():
    pass

def function_b():
    class C1(object):
        class C2(object):
            pass
        ''')
    quality.core.annotate_qualnames(tree)
    assert_equal('<module>', tree.qualname)
    assert_equal('function_a', tree.body[0].qualname)
    assert_equal('function_b', tree.body[1].qualname)
    assert_equal('function_b.C1', tree.body[1].body[0].qualname)
    assert_equal('function_b.C1.C2', tree.body[1].body[0].body[0].qualname)

def test_find_contestants():
    # because annotate_linenums and the like inject attributes into the AST nodes
    # after we run ast.parse, we need to recreate those attributes so we don't hit
    # AttributeErrors.  This sucks; we can fix it by not adding stuff to the AST tree.
    def add_missing_attribs(node):
        node.linenums = node.qualname = node.descendant_lines = None
        for child in ast.iter_child_nodes(node):
            add_missing_attribs(child)
    tree = ast.parse('''
class C:
    def method_a(self):
        if True == False:
            def function_b():
                pass
        def function_c():
            pass
''')
    add_missing_attribs(tree)

    contestants = quality.core.find_contestants(tree)
    assert_equal(5, len(contestants))
    assert_equal(['Module', 'ClassDef', 'FunctionDef', 'FunctionDef', 'FunctionDef'],
        [i.node.__class__.__name__ for i in contestants])
    
def test_extract_line_nums():
    doc = xml.etree.ElementTree.ElementTree(element=xml.etree.ElementTree.fromstring('''<?xml version="1.0" ?>
<!DOCTYPE coverage
  SYSTEM 'http://cobertura.sourceforge.net/xml/coverage-03.dtd'>
<coverage>
    <packages>
        <package>
            <classes>
                <class branch-rate="0" complexity="0" filename="/tmp/something_a.py" line-rate="0.9305" name="something_a">
                    <methods/>
                    <lines>
                        <line hits="1" number="7"/>
                        <line hits="0" number="8"/>
                        <line hits="1" number="9"/>
                    </lines>
                </class>
            </classes>
        </package>
        <package>
            <classes>
                <class branch-rate="0" complexity="0" filename="/usr/lib/python2.7/site-packages/something_b.py" line-rate="0.9305" name="something_b">
                    <methods/>
                    <lines>
                        <line hits="0" number="7"/>
                        <line hits="1" number="8"/>
                        <line hits="1" number="9"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>'''))

    assert_equal((set([7, 9]), set([8])), quality.crap.extract_line_nums(doc, '/tmp/something_a.py'))
    assert_equal((set([8, 9]), set([7])), quality.crap.extract_line_nums(doc, '/usr/lib/python2.7/site-packages/something_b.py'))
    with assert_raises(ValueError) as assert_context:
        quality.crap.extract_line_nums(doc, 'non-existent-file')
    assert_equal('couldn\'t find coverage data for source file "non-existent-file" in coverage.xml document', assert_context.exception.args[0])


def test_extract_judge_kwargs():
    assert_equal({}, quality.core.extract_judge_kwargs('hello', {}))
    assert_equal(
        {}, 
        quality.core.extract_judge_kwargs(
            'hello', 
            {'goodbye:something': 1}
        )
    )
    assert_equal(
        {
            'thing': 1,
            'otherthing': 2,
        }, 
        quality.core.extract_judge_kwargs(
            'hello', 
            {
                'goodbye:something': 1,
                'goodbye:somethingelse': 2,
                'hello:thing': 1,
                'hello:otherthing': 2,
            }
        )
    )

@mock.patch('__builtin__.open', spec=file)
@mock.patch('ast.parse')
@mock.patch('xml.etree.ElementTree.parse')
@mock.patch.multiple(
    'quality.core', 
    annotate_qualnames=mock.MagicMock(spec=quality.core.annotate_qualnames), 
    annotate_linenums=mock.MagicMock(spec=quality.core.annotate_linenums),
    find_contestants=mock.MagicMock(spec=quality.core.find_contestants),
)
def test_run_contest(etree_parse, ast_parse, mock_open):
    contestant_a = mock.MagicMock(name='contestant a')
    contestant_a.name = 'function_a'
    contestant_b = mock.MagicMock(name='contestant b')
    contestant_b.name = 'function_b'
    contestants = [contestant_a, contestant_b]
    quality.core.find_contestants.return_value = contestants

    def mock_judge(contestant, **options):
        '''
        replace the return value of mock judges
        '''
        qualities = {
            'function_a': 2,
            'function_b': 1,
        }
        return qualities[contestant.name]

    judge = mock.MagicMock(side_effect=mock_judge)
    judge.name = 'mock_judge_name'

    src_path = '/path/to/src.py'
    result = quality.core.run_contest([src_path], {}, '2*mock_judge_name', [judge])

    mock_open.assert_called_once_with(src_path)
    mock_open.read.assert_called_once()
    # ast_parse.assert_called_once_with(mock_open.read.return_value, filename=src_path)
    ast_parse.assert_called_once()
    quality.core.annotate_qualnames.assert_called_once_with(ast_parse.return_value)
    quality.core.annotate_linenums.assert_called_once_with(ast_parse.return_value)
    quality.core.find_contestants.assert_called_once_with(ast_parse.return_value)
    
    assert_equal(
        result,
        {
            '/path/to/src.py': [
                contestant_b,
                contestant_a,
            ]
        }
    )
    assert_equal(4, contestant_a.final_score)
    assert_equal(2, contestant_b.final_score)