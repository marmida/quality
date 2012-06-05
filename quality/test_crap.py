import quality.crap

import ast
import mock
from nose.tools import *
import xml.etree.ElementTree


def test_contestant_align_linenums():
    def execute(expected, contestant_lines, coverage_lines):
        # set-ify everything
        expected = set(expected)
        contestant_lines = set(contestant_lines)
        coverage_lines = {
            'foo.py': set(coverage_lines)
        }

        j = quality.crap.CrapJudge()
        j.unified = coverage_lines
        contestant = mock.MagicMock(linenums=contestant_lines, src_file='foo.py')

        assert_equal(expected, j.align_linenums(contestant))

    args_ls = [
        # obvious cases
        ([], [], []),
        ([1, 2, 3], [1, 2, 3], [1, 2, 3]),

        # coverage.xml lists one of a multi-line statement, for which we have multiple lines
        ([2], [1, 2, 3], [2]),
    ]

def test_contestant_coverage_ratio():
    def execute(expected, hit, miss, contestant_lines):
        # set-ify everything
        hit = set(hit)
        miss = set(miss)
        contestant_lines = set(contestant_lines)

        j = quality.crap.CrapJudge()
        j.align_linenums = mock.MagicMock()
        j.align_linenums.return_value = contestant_lines
        j.coverage['foo.py'] = (hit, miss)
        j.unified['foo.py'] = hit | miss

        contestant = mock.MagicMock(linenums=contestant_lines, src_file='foo.py')

        assert_equal(expected, j.coverage_ratio(contestant))
        if contestant_lines:
            j.align_linenums.assert_called_once_with(contestant)

    args_ls = [
        (0.5, [15, 16], [5, 6], [5, 6, 15, 16]),
        (0.0, [4, 5, 6], [], [1, 2, 3]),
        # checking for divide-by-zero
        (1.0, [], [], []),
    ]
    for args in args_ls:
        execute(*args)

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
