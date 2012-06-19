'tests for lint.py'

from __future__ import absolute_import

import quality.lint

import os.path
from nose.tools import *

PROB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'tabnanny_problems.py')

def test_run_pylint():
    output = quality.lint.run_pylint(PROB_FILE)
    for line in output:
        if 'Found indentation with tabs instead of spaces' in line:
            break
    else:
        assert False, 'Did not find expected message in pylint output'

