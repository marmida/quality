'Covers report.py'

import math
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
                ['ab', 123, 4],
                ['cdef', 42, 424242],
            ],
            '''\
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