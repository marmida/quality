from nose.tools import *

import quality.dec

def test_judge():
    @quality.dec.judge('meep')
    def judge_fn():
        pass

    assert_equal('meep', judge_fn._quality_judge_name)