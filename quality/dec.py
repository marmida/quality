'''
quality's kinda-sorta API layer
'''

# todo: because OutputCollectingJudge doesn't use this anymore, this may not be a good idea
class JudgeDecorator(object):
    def __init__(self, judge_name):
        self.judge_name = judge_name

    def __call__(self, fn):
        def wrapped(*args, **kwargs):
            return fn(*args, **kwargs)
        wrapped._quality_judge_name = self.judge_name
        return wrapped

judge = JudgeDecorator    