'''
this module is for use by test_quality.py
dynamically generated code doesn't get line numbers, and we need that to line up with 
coverage.py's output.  I can't think of a sane way to achieve that without using the filesystem.
'''

def afunc(arg):
    print 'you sent this arg: %s' % arg

def bfunc():
    def innerfunc(x):
        print 'a function inside another function!'
    print 'this is bfunc'

class SomeClass(object):
    def __init__(self):
        print 'this is SomeClass.__init__'

    def amethod(self):
        print 'this is SomeClass.amethod'

    def bmethod(self):
        print 'this is SomeClass.bmethod'
