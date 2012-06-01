import quality.crap

import ast
from nose.tools import *
import xml.etree.ElementTree


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
