'Tests for indentation.py'

import quality.indentation

from nose.tools import *
import os.path

CUR_PATH = os.path.abspath(__file__)
TABNANNY_PROB_PATH = os.path.join(os.path.dirname(CUR_PATH), 'data', 'tabnanny_problems.py')
INDENT_ERROR_PATH = os.path.join(os.path.dirname(CUR_PATH), 'data', 'indentation_error.py')


def test_run_tabnanny():
    'TabnannyJudge.run_tabnanny: correctly updates results cache'
    j = quality.indentation.TabnannyJudge()
    j.run_tabnanny(INDENT_ERROR_PATH)
    assert_equal({INDENT_ERROR_PATH: True}, j.results)
    j.run_tabnanny(TABNANNY_PROB_PATH)
    assert_equal({TABNANNY_PROB_PATH: True, INDENT_ERROR_PATH: True}, j.results)
    j.run_tabnanny(CUR_PATH)
    assert_equal({TABNANNY_PROB_PATH: True, INDENT_ERROR_PATH: True, CUR_PATH: False}, j.results)