'Covers report.py'

import math
import mock
from nose.tools import *
import StringIO

import quality.report

def _test_ordered_scores(scores, judge_names, expected):
    assert_equal(expected, quality.report.ordered_scores(scores, judge_names))

def test_ordered_scores():
    'ordered_scores: correctly sorts and extracts scores'
    args_ls = [
        ({}, [], []),
        ({'abc': 1}, ['abc'], [1]),
        ({'abc': 1, 'def': 2}, ['def', 'abc'], [2, 1]),
        ({'a': 1, 'b': 2, 'c': 3}, ['c', 'a', 'b'], [3, 1, 2])
    ]
    for args in args_ls:
        yield (_test_ordered_scores,) + args

def _test_write_minimal_columns(chart, expected):
    actual = StringIO.StringIO()
    quality.report.write_minimal_columns(chart, actual)
    assert_equal(expected, actual.getvalue())

def test_write_minimal_columns():
    'write_minimal_columns: correctly sizes column widths'
    args_ls = [
        ([], ''),
        ([['abc', 'def']], 'abc  def\n'),
        (
            [
                ['abc', 'def', 'ghi'],
                ['hello', 'goodbye', 'goodnight'],
            ],
            '''\
abc    def      ghi      
hello  goodbye  goodnight
'''
        ),
        (
            [
                ['Name', 'Ego', 'Id'],
                ['ab', 123, 4],
                ['cdef', 42, 424242],
            ],
            '''\
Name  Ego      Id
ab    123       4
cdef   42  424242
'''
        ),
        (
            [['abc', math.pi]],
         '''\
abc  3.142
'''
        ),
    ]
    for args in args_ls:
        yield (_test_write_minimal_columns,) + args

def test_print_report():
    'print_report: builds and sorts data necessary for write_minimal_columns'
    # no data test: should not do anything with no results
    with mock.patch('sys.stdout') as mock_stdout:
        with mock.patch('quality.report.write_minimal_columns') as mock_write_minimal_columns:
            quality.report.print_report({})

    assert_equal(0, mock_write_minimal_columns.call_count)

    # data test: should behave when called with results
    def make_contestant(name, wibblyness, wobblyness, final):
        contestant = mock.MagicMock(scores={'wibblyness': wibblyness, 'wobblyness': wobblyness}, final_score=final)
        contestant.name = name # can't set this via constructor kwargs
        return contestant

    contestant1 = make_contestant('function_a', 4, 2.0, 6)
    contestant2 = make_contestant('function_b', 8, 2.2, 8)
    contestant3 = make_contestant('function_c', 12, 4.1, 7)

    # problem: either wibbyness or wobblyness will show up in the chart first, 
    # depending on the order returned by the first contestant's keys()
    # this approach isn't very DRY; maybe there's a better way?
    names = contestant1.scores.keys()
    expected = [
        ['File', 'Item', 'wibblyness', 'wobblyness', 'Final'],
        ['file1.py', 'function_b', 8, 2.2, 8],
        ['file2.py', 'function_c', 12, 4.1, 7], # function C should get sorted between A and B
        ['file1.py', 'function_a', 4, 2.0, 6],
    ] if names[0] == 'wibblyness' else [
        ['File', 'Item', 'wobblyness', 'wibblyness', 'Final'],
        ['file1.py', 'function_b', 2.2, 8, 8],
        ['file2.py', 'function_c', 4.1, 12, 7],
        ['file1.py', 'function_a', 2.0, 4, 6],
    ]
    
    results = {
        'file1.py': [
            contestant1,
            contestant2,
        ],
        'file2.py': [
            contestant3,
        ]
    }

    with mock.patch('sys.stdout') as mock_stdout:
        with mock.patch('quality.report.write_minimal_columns') as mock_write_minimal_columns:
            quality.report.print_report(results)

    mock_write_minimal_columns.assert_called_once_with(expected, mock_stdout)