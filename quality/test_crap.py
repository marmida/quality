import quality.crap

import ast
import mock
from nose.tools import *
import xml.etree.ElementTree


def _crapjudge_align_linenums(expected, contestant_lines, coverage_lines):
    'run one test of CrapJudge.align_linenums'
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

def test_gen_crapjudge_align_linenums():
    'CrapJudge.align_linenums: filters out linenums not in coverage.xml'
    args_ls = [
        # obvious cases
        ([], [], []),
        ([1, 2, 3], [1, 2, 3], [1, 2, 3]),

        # coverage.xml lists one of a multi-line statement, for which we have multiple lines
        ([2], [1, 2, 3], [2]),
    ]

    for args in args_ls:
        yield (_crapjudge_align_linenums,) + args

def test_gen_crapjudge_coverage_ratio():
    'CrapJudge.coverage_ratio: correctly calculates coverage ratio'
    args_ls = [
        (0.5, [15, 16], [5, 6], [5, 6, 15, 16]),
        (0.0, [4, 5, 6], [], [1, 2, 3]),
        # checking for divide-by-zero
        (1.0, [], [], []),
    ]
    for args in args_ls:
        yield (_crapjudge_coverage_ratio,) + args
    
def _crapjudge_coverage_ratio(expected, hit, miss, contestant_lines):
    'Runs one test of CrapJudge.coverage ratio'
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

def test_crapjudge_judge_crap():
    pass

def test_extract_line_nums():
    'extract_line_nums: correctly splits hit and missed lines, per file'
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
