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
    ok_(
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
def test_enumerate_module():
    import test_enumerate_routines_2
    ok_(
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
    
@unittest.expectedFailure
def test_quality():
	ok_(
		quality.quality(
			'/home/marmida/develop/chickenfoot/chickenfoot.py',
			'/home/marmida/develop/chickenfoot/test_chickenfoot.py',
		),
		0
	)