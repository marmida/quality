import quality

from nose.tools import *
import os.path
import sys
import unittest

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

def setup():
    sys.path.append(DATA_DIR)

def teardown():
    sys.path.pop()

@with_setup(setup, teardown)
def test_enumerate_module():
    import test_enumerate_routines_1
    assert_equal(
        quality.enumerate_module('test_enumerate_routines_1'),
        {
            'afunc': (test_enumerate_routines_1.afunc, [6, 7], {}),
            'bfunc': (test_enumerate_routines_1.bfunc, [9, 10, 11, 12], {}), # note that "innerfunc" doesn't show up
            'SomeClass': 
                (
                    test_enumerate_routines_1.SomeClass, 
                    [],
                    {
                        '__init__': (test_enumerate_routines_1.SomeClass.__init__, [15, 16], {}),
                        'amethod': (test_enumerate_routines_1.SomeClass.amethod, [18, 19], {}),
                        'bmethod': (test_enumerate_routines_1.SomeClass.bmethod, [21, 22], {}),
                    }
                ),
        }
    )

@with_setup(setup, teardown)
def test_enumerate_nested_classes():
    import test_enumerate_routines_2
    assert_equal(
        quality.enumerate_module('test_enumerate_routines_2'),
        {
            'Outer': 
                (
                    test_enumerate_routines_2.Outer, 
                    [],
                    {
                        'do_something': (test_enumerate_routines_2.Outer.do_something, [3, 4], {}),
                        'Inner': 
                            (
                                test_enumerate_routines_2.Outer.Inner,
                                [],
                                {
                                    'do_something': (test_enumerate_routines_2.Outer.Inner.do_something, [6, 7], {}),
                                },
                            ),
                    }
                ),
        }
    )

@with_setup(setup, teardown)
def test_enumerate_extramodule_code():
    import test_enumerate_routines_3
    assert_equal(
        quality.enumerate_module('test_enumerate_routines_3'),
        {
            'Child': (test_enumerate_routines_3.Child, [8, 9], {}),
            'Child2': 
                (
                    test_enumerate_routines_3.Child2,
                    [],
                    {
                        'another_function': (
                            test_enumerate_routines_3.Child2.another_function,
                            [12, 13],
                            {}
                        ),
                    }
                ),
        }
    )

def test_union_line_nums():
    assert_equal(
        quality.union_line_nums(
            {
                'what': (lambda x: x, [1, 2, 3], {}),
            }
        ),
        set([1, 2, 3]),
    )
    assert_equal(
        quality.union_line_nums(
            {
                'what': (
                    lambda x: x, 
                    [1, 2, 3], 
                    {
                        'where': (lambda x: x, [3], {})
                    }),
            }
        ),
        set([1, 2, 3]),
    )
    assert_equal(
        quality.union_line_nums(
            {
                'what': (
                    lambda x: x, 
                    [1, 2, 3], 
                    {
                        'where': (lambda x: x, [4], {})
                    }),
            }
        ),
        set([1, 2, 3, 4]),
    )
    assert_equal(
        quality.union_line_nums(
            {
                'what': (lambda x: x, [1, 2, 3], {}),
                'when': (lambda x: x, [4, 5], {}),
                'why': (lambda x: x, [6], {}),
            }
        ),
        set([1, 2, 3, 4, 5, 6]),
    )

@unittest.expectedFailure
def test_quality():
	ok_(
		quality.quality(
			'/home/marmida/develop/chickenfoot/chickenfoot.py',
			'/home/marmida/develop/chickenfoot/test_chickenfoot.py',
		),
		0
	)