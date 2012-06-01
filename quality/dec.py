'''
quality's kinda-sorta API layer
'''

class JudgeDecorator(object):
    def __init__(self, judge_name):
        self.judge_name = judge_name

    def __call__(self, fn):
        def wrapped(*args, **kwargs):
            return fn(*args, **kwargs)
        wrapped._quality_judge_name = self.judge_name
        return wrapped

judge = JudgeDecorator    