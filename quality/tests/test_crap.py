import quality.core
import quality.crap

import ast
import mock
from nose.tools import *
import os
import os.path
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

def _test_crapjudge_judge_crap_cached(mock_complexity_ret, mock_cov_ratio_ret, expected):
    'run one test over CrapJudge.judge_crap, in which coverage data is already cached'
    mock_node = mock.MagicMock(name='node')
    contestant = mock.MagicMock(spec=quality.core.Contestant, linenums=set([1, 2, 3]), 
        src_file='foo.py', node=mock_node)
    judge = quality.crap.CrapJudge()

    # line numbers in the coverage data cache don't matter, just that they exist.
    judge.coverage = {
        'foo.py': (set([1, 2, 3]), set()),
        'bar.py': (set([4, 5, 6]), set()),
    }
    judge.unified = {
        'foo.py': set([1, 2, 3]),
        'bar.py': judge.coverage['bar.py'][0],
    }
    judge.coverage_ratio = mock.MagicMock(return_value=mock_cov_ratio_ret)
    
    # create a mock for parse that should not be called
    tripwire_etree_parse = mock.patch('xml.etree.ElementTree.parse', 
        name='tripwire_etree_parse',
        side_effect=Exception('judge_crap attempted to re-parse XML; should have used cached data instead')
    )

    with tripwire_etree_parse:
        with mock.patch('quality.complexity.complexity', return_value=mock_complexity_ret):
            assert_equal(expected, judge.judge_crap(contestant, coverage_file='coverage.xml'))
            quality.complexity.complexity.assert_called_once_with(mock_node)
            judge.coverage_ratio.assert_called_once_with(contestant)

def test_gen_crapjudge_judge_crap_cached():
    'CrapJudge.judge_crap: uses cached coverage info to calculate scores'
    args_ls = [
        # trials that should not attempt to re-parse data
        (4, 1.0, 4),
        (4, 0.5, 12),
    ]

    for args in args_ls:
        yield (_test_crapjudge_judge_crap_cached,) + args

def _test_crapjudge_judge_crap_uncached(mock_complexity_ret, mock_cov_ratio_ret, expected):
    '''
    Run one test over CrapJudge.judge_crap, in which coverage data isn't cached.

    Yes, this repeats a lot of the code in _test_crapjudge_judge_crap_cached, but
    I'm less opposed to copy-pasta than complication in test fixtures.
    '''
    mock_node = mock.MagicMock(name='node')
    contestant = mock.MagicMock(spec=quality.core.Contestant, linenums=set([1, 2, 3]), 
        src_file='foo.py', node=mock_node)
    judge = quality.crap.CrapJudge()

    # line numbers in the coverage data cache don't matter, just that they exist.
    judge.coverage = {
        'bar.py': (set([4, 5, 6]), set()),
    }
    judge.unified = {
        'bar.py': judge.coverage['bar.py'][0],
    }
    judge.coverage_ratio = mock.MagicMock(return_value=mock_cov_ratio_ret)
    
    # create a mock for the (hit, miss) line number sets
    mock_union = mock.MagicMock(name='union')
    mock_hit = mock.MagicMock(name='mock_hit')
    mock_miss = mock.MagicMock(name='mock_miss')
    mock_hit.__or__ = mock.MagicMock(return_value=mock_union)

    with mock.patch('xml.etree.ElementTree.parse', name='mock_etree_parse') as mock_etree_parse:
        with mock.patch('quality.complexity.complexity', return_value=mock_complexity_ret):
            with mock.patch('quality.crap.extract_line_nums', return_value=(mock_hit, mock_miss)):
                assert_equal(expected, judge.judge_crap(contestant, coverage_file='coverage.xml'))
                quality.complexity.complexity.assert_called_once_with(mock_node)
                judge.coverage_ratio.assert_called_once_with(contestant)
                mock_etree_parse.assert_called_once_with('coverage.xml')
                assert_equal((mock_hit, mock_miss), judge.coverage['foo.py'])
                assert_equal(mock_union, judge.unified['foo.py'])

def test_gen_crapjudge_judge_crap_uncached():
    'CrapJudge.judge_crap: populates coverage data cache and calculates scores'
    args_ls = [
        # trials that should not attempt to re-parse data
        (4, 1.0, 4),
        (4, 0.5, 12),
    ]

    for args in args_ls:
        yield (_test_crapjudge_judge_crap_uncached,) + args

def _test_find_class_elem(doc, source_path, coverage_file, expected_elem_name):
    actual = quality.crap.find_class_elem(doc, source_path, coverage_file)
    assert_equal(actual.get('name'), expected_elem_name)

def test_find_class_elem():
    'find_class_elem: identifies the correct <class> element using either relative and absolute paths'
    doc = xml.etree.ElementTree.ElementTree(element=xml.etree.ElementTree.fromstring('''<?xml version="1.0" ?>
<!DOCTYPE coverage
  SYSTEM 'http://cobertura.sourceforge.net/xml/coverage-03.dtd'>
<coverage>
    <packages>
        <package>
            <classes>
                <class filename="/tmp/something_a.py" name="something_a"/>
                <class filename="/tmp/something_b.py" name="something_b"/>
            </classes>
        </package>
        <package>
            <classes>
                <class filename="something_c.py" name="something_c"/>
                <class filename="src/something_d.py" name="something_d"/>
            </classes>
        </package>
    </packages>
</coverage>'''))

    args_ls = [
        # absolute paths should work
        (doc, '/tmp/something_a.py', 'coverage.xml', 'something_a'),
        (doc, '/tmp/something_b.py', '/tmp/something/else/coverage.xml', 'something_b'),
        # relative path combinations in which coverage.xml and the source file are in the same dir
        (doc, 'src/something_c.py', 'src/coverage.xml', 'something_c'),
        (doc, 'something_c.py', 'coverage.xml', 'something_c'),
        (doc, 'src/something_c.py', './src/coverage.xml', 'something_c'),
        (doc, './src/something_c.py', 'src/coverage.xml', 'something_c'),
        # relative path combinations in which coverage.xml and the source file are in different dirs
        (doc, 'src/something_d.py', 'coverage.xml', 'something_d'),
        (doc, 'src/something_d.py', './coverage.xml', 'something_d'),
        (doc, './src/something_d.py', 'coverage.xml', 'something_d'),
        # (doc, 'something_d.py', '../coverage.xml', 'something_d'), # not certain about this case; 
        # it probably should be allowed
    ]
    for args in args_ls:
        yield (_test_find_class_elem,) + args

    with assert_raises(ValueError) as assert_context:
        quality.crap.find_class_elem(doc, 'non-existent-file', '/tmp/coverage.xml')
    assert_equal('couldn\'t find coverage data for source file "non-existent-file" in coverage.xml document', assert_context.exception.args[0])

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

    assert_equal((set([7, 9]), set([8])), quality.crap.extract_line_nums(doc, '/tmp/something_a.py', 'coverage.xml'))
    assert_equal((set([8, 9]), set([7])), quality.crap.extract_line_nums(doc, '/usr/lib/python2.7/site-packages/something_b.py', 'coverage.xml'))