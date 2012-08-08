'Tests for indentation.py'

from __future__ import absolute_import

import quality.tabnanny
import quality.tests.compat # must come before import nose.tools

import mock
from nose.tools import *
import os
import os.path
import StringIO

CUR_PATH = os.path.abspath(__file__)
TABNANNY_PROB_PATH = os.path.join(os.path.dirname(CUR_PATH), 'data', 'tabnanny_problems.py')
INDENT_ERROR_PATH = os.path.join(os.path.dirname(CUR_PATH), 'data', 'indentation_error.py')

def test_run_tabnanny():
    'run_tabnanny: returns the captured stdout from tabnanny'
    def get_file_len(fobj):
        fobj.seek(0, os.SEEK_END)
        return fobj.tell()
    
    # the current file should have no problems, and should result in an empty stdout
    assert_equal(0, get_file_len(quality.tabnanny.run_tabnanny(CUR_PATH)))
    # both of the two bad files should yield some output without exiting or raising
    assert get_file_len(quality.tabnanny.run_tabnanny(TABNANNY_PROB_PATH))
    assert get_file_len(quality.tabnanny.run_tabnanny(INDENT_ERROR_PATH))

def test_tabnannyjudge_call():
    'TabnannyJudge.run_tabnanny: correctly updates results cache'
    j = quality.tabnanny.TabnannyJudge()
    # put some bogus data in the judge
    j['abc'] = StringIO.StringIO('')
    j['def'] = StringIO.StringIO('something happened!')
    assert_equal(0, j(mock.MagicMock(src_file='abc')))
    assert_equal(1, j(mock.MagicMock(src_file='def')))