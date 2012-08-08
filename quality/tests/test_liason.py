from __future__ import absolute_import

import quality.liason
import quality.tests.compat # must come before import nose.tools

import mock
from nose.tools import *
import os
import StringIO
import sys

def test_patchcontext():
    orig = mock.MagicMock(name='sub')
    parent = mock.MagicMock(name='parent', sub=orig)
    replacement = mock.MagicMock(name='replacement')

    with quality.liason.PatchContext(parent, 'sub', replacement):
        assert_equal(replacement, parent.sub)
    assert_equal(orig, parent.sub)

    # ensure that exiting via an exception still restores original
    class BogusException(Exception):
        pass

    try:
        with quality.liason.PatchContext(parent, 'sub', replacement):
            raise BogusException
    except BogusException:
        pass
    assert_equal(orig, parent.sub)

def test_capture_output():
    'capture_output: works to return a StringIO of stderr'
    # define and decorate some functions
    @quality.liason.capture_output
    def stdout_writer():
        sys.stdout.write('hello\n')
    @quality.liason.capture_output
    def noop():
        pass

    # fetch the contents of stdout
    assert_equal('hello\n', stdout_writer().getvalue())
    # ensure that returned files are rewound
    assert_equal(0, stdout_writer().tell())
    # ensure everything still works when nothing is written
    assert_equal('', noop().getvalue())

def test_filteredfileproxy():
    'FilteredFileProxy: prevents writing certain strings'
    buf = StringIO.StringIO()
    p = quality.liason.FilteredFileProxy(buf, 'Pintsize')
    p.write('Marten\n')
    p.write('Pintsize\n')
    assert 'Pintsize' not in buf.getvalue()
    p.writelines(['Hannelore\n', 'Faye\n', 'Pintsize\n', 'Dora\n'])
    assert 'Pintsize' not in buf.getvalue()

    # try again without newlines
    p = quality.liason.FilteredFileProxy(buf, 'Pintsize')
    p.write('Marten')
    p.write('Pintsize')
    assert 'Pintsize' not in buf.getvalue()
    p.writelines(['Hannelore', 'Faye', 'Pintsize', 'Dora'])
    assert 'Pintsize' not in buf.getvalue()

    # proxying should allow normal methods to work
    p.seek(0, os.SEEK_END)
    assert_equal(p.tell(), len(buf.getvalue()))

    # proxying should not break normal errors
    with assert_raises(AttributeError):
        p.non_existent()

def test_outputcollectingjudge_keydefaultdict():
    'OutputCollectingJudge: still behaves like a defaultdict, but provides the key to default_factory'
    with assert_raises(KeyError):
        quality.liason.OutputCollectingJudge('bogus')[1]
    
    d = quality.liason.OutputCollectingJudge('bogus')
    d['abc'] = 123
    assert_equal(123, d['abc'])

    factory = mock.MagicMock(side_effect=lambda x: x**2)
    d = quality.liason.OutputCollectingJudge('bogus', factory)
    # grab two keys, twice each
    assert_equal(4, d[2])
    assert_equal(4, d[2])
    assert_equal(16, d[4])
    assert_equal(16, d[4])

    # the mock should only have been called twice
    # we don't assert the entire list, because it collects other calls from the defautdict machinery
    assert_equal(1, factory.call_args_list.count(mock.call(2)))
    assert_equal(1, factory.call_args_list.count(mock.call(4)))

def test_outputcollectingjudge_call():
    'OutputCollectingJudge: base implementation of __call__ raises NotImplementedError'
    with assert_raises(NotImplementedError):
        quality.liason.OutputCollectingJudge('bogus')(mock.MagicMock())