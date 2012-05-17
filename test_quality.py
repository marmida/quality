import quality

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
    quality.annotate_linenums(tree)
    assert_equal([7, 8], tree.descendant_lines)
    assert_equal([2], tree.body[0].descendant_lines)
    assert_equal([5], tree.body[1].descendant_lines)

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
    quality.annotate_linenums(tree)
    assert_equal([], tree.descendant_lines)
    assert_equal([3], tree.body[0].descendant_lines)
    assert_equal([5, 15], tree.body[0].body[1].descendant_lines)
    # line 10 isn't part of the next assertion, because it's not a statement
    assert_equal([7, 14], tree.body[0].body[1].body[1].descendant_lines)

def test_annotate_linenums_docstrings():
    tree = ast.parse(''''module docstring'
pass

def dosomething():
    \'\'\'
    multi-line function docstring
    \'\'\'
    pass
''')
    quality.annotate_linenums(tree)
    assert_equal([2], tree.descendant_lines)
    assert_equal([8], tree.body[2].descendant_lines)

def test_annotate_linenums_multiline():
    '''
    annotate_linenums: multi-line statements should only be counted against the initial 
    line, in order to coincide with coverage.xml
    '''
    tree = ast.parse('''
a = b = \\
    c = \\
    3''')
    quality.annotate_linenums(tree)
    assert_equal([2], tree.descendant_lines)

def test_annotate_qualnames():
    tree = ast.parse('''
def function_a():
    pass

def function_b():
    class C1(object):
        class C2(object):
            pass
        ''')
    quality.annotate_qualnames(tree)
    assert_equal('<module>', tree.qualname)
    assert_equal('function_a', tree.body[0].qualname)
    assert_equal('function_b', tree.body[1].qualname)
    assert_equal('function_b.C1', tree.body[1].body[0].qualname)
    assert_equal('function_b.C1.C2', tree.body[1].body[0].body[0].qualname)

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
    quality.CCAnnotator().visit(tree)
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
    quality.CCAnnotator().visit(tree)
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
    quality.CCAnnotator().visit(tree)
    assert_equal(1, tree.complexity)
    assert_equal(2, tree.body[1].complexity)
    assert_equal(1, tree.body[1].body[1].complexity)

def test_find_defs():
    tree = ast.parse('''
class C:
    def method_a(self):
        if True == False:
            def function_b():
                pass
        def function_c():
            pass
''')

    defs = []
    quality.find_defs(tree, defs)
    assert_equal(5, len(defs))
    assert_equal(['Module', 'ClassDef', 'FunctionDef', 'FunctionDef', 'FunctionDef'],
        [i.__class__.__name__ for i in defs])
    # differentiate the FunctionDefs by name
    assert_equal('method_a', defs[2].name)
    assert_equal('function_b', defs[3].name)
    assert_equal('function_c', defs[4].name)

def test_extract_hit_lines():
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

    assert_equal(set([7, 9]), quality.extract_hit_lines(doc, '/tmp/something_a.py'))
    assert_equal(set([8, 9]), quality.extract_hit_lines(doc, '/usr/lib/python2.7/site-packages/something_b.py'))
    with assert_raises(ValueError) as assert_context:
        quality.extract_hit_lines(doc, 'non-existent-file')
    assert_equal('couldn\'t find coverage data for source file "non-existent-file" in coverage.xml document', assert_context.exception.args[0])

def test_calc_coverage_ratio():
    assert_equal(0.5, quality.calc_coverage_ratio([5, 6, 15, 16], set([15, 16])))
    assert_equal(0.0, quality.calc_coverage_ratio([4, 5, 6], set([1, 2, 3])))
    # checking for divide-by-zero
    assert_equal(1.0, quality.calc_coverage_ratio([], set([])))

@mock.patch('__builtin__.open', spec=file)
@mock.patch('ast.parse')
@mock.patch('xml.etree.ElementTree.parse')
@mock.patch.multiple(
    'quality', 
    annotate_qualnames=mock.MagicMock(spec=quality.annotate_qualnames), 
    annotate_linenums=mock.MagicMock(spec=quality.annotate_linenums),
    CCAnnotator=mock.MagicMock(spec=quality.CCAnnotator),
    calc_coverage_ratio=mock.MagicMock(spec=quality.calc_coverage_ratio, side_effect=[0.0, 1.0]),
    extract_hit_lines=mock.MagicMock(spec=quality.extract_hit_lines),
)
def test_quality(etree_parse, ast_parse, mock_open):
    # find_defs is weird, because it generates side effects
    found_defs = [
        mock.MagicMock(
            descendant_lines=[1, 2, 3],
            qualname='function_a',
            complexity=4,
        ), 
        mock.MagicMock(
            descendant_lines=[4, 5, 6],
            qualname='function_b',
            complexity=31,
        ),
    ]
    def set_find_defs(src_tree, defs):
        defs += found_defs
        
    coverage_xml_path, src_path = '/path/to/coverage.xml', '/path/to/src.py'
    with mock.patch('quality.find_defs', new=mock.MagicMock(side_effect=set_find_defs)) as mock_find_defs:
        result = quality.quality(coverage_xml_path, src_path)


    etree_parse.assert_called_once_with(coverage_xml_path)
    quality.extract_hit_lines.assert_called_once_with(etree_parse.return_value, src_path)
    mock_open.assert_called_once_with(src_path)
    mock_open.read.assert_called_once()
    # ast_parse.assert_called_once_with(mock_open.read.return_value, filename=src_path)
    ast_parse.assert_called_once()
    quality.annotate_qualnames.assert_called_once_with(ast_parse.return_value)
    quality.annotate_linenums.assert_called_once_with(ast_parse.return_value)
    quality.CCAnnotator.return_value.visit.assert_called_once_with(ast_parse.return_value)
    assert_equal(mock_find_defs.call_args_list[0][0][0], ast_parse.return_value)

    assert_equal(
        quality.calc_coverage_ratio.call_args_list,
        [
            mock.call(found_defs[0].descendant_lines, quality.extract_hit_lines.return_value),
            mock.call(found_defs[1].descendant_lines, quality.extract_hit_lines.return_value),
        ]
    )

    assert_equal(
        result,
        [
            ('function_a', 20),
            ('function_b', 31),
        ]
    )