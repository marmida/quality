'Routines related to collecting stdout/stderr from other programs'

from __future__ import absolute_import

import collections
import StringIO
import sys
import types

class PatchContext(object):
    'A context manager that swaps out one object on entry, and restores the original on exit.'
    def __init__(self, obj, attr_name, replacement):
        self.obj = obj
        self.attr_name = attr_name
        self.replacement = replacement

    def __enter__(self):
        self.orig = getattr(self.obj, self.attr_name)
        setattr(self.obj, self.attr_name, self.replacement)
        return self

    def __exit__(self, exc_type, exc_val, tb):
        setattr(self.obj, self.attr_name, self.orig)

def capture_output(fn):
    '''
    Enter a context-managed capture of stdout, and then dispatch to the 
    original function.

    Meant to be used as a decorator for default_factory functions for
    OutputCollectingJudge.
    '''
    def wrapped(*args, **kwargs):
        output_buffer = StringIO.StringIO()
        with PatchContext(sys, 'stdout', output_buffer):
            fn(*args, **kwargs)
        output_buffer.seek(0)
        return output_buffer
    return wrapped

class FilteredFileProxy(object):
    '''
    A proxy for a file-like object that hooks into the write methods to 
    exclude certain strings.

    This is a brittle solution, because we're counting on the search string
    being written in a single call, e.g. when searching for "Can't touch this",
    we would miss a call to obj.writelines(["Can't ", "touch ", "this"]).

    Note that one can't patch only these methods on true file-like objects,
    since those are built-ins, and thus their attributes are read-only.
    '''
    def __init__(self, orig, search):
        '''
        Args:
        * `orig` - the original file object being proxied
        * `search` - the string to filter out from write calls
        '''
        self._orig = orig
        self._search = search
        def filtered_write(self, output):
            if output.endswith('\n'):
                output = output[:-1]
            if output == self._search:
                return
            orig.write(output)
        def filtered_writelines(self, seq):
            orig.writelines(output for output in seq if output != self._search
                and not (output.endswith('\n') and output[:-1] == self._search))
        self._filters = {
            'write': types.MethodType(filtered_write, self),
            'writelines': types.MethodType(filtered_writelines, self),
        }

    def __getattr__(self, attrname):
        if attrname in self._filters:
            return self._filters[attrname]
        return getattr(self._orig, attrname)


class OutputCollectingJudge(collections.defaultdict):
    '''
    Combines two concepts for judging programs that write to stdout.

    First, this object is a dict that is meant to map Contestants 
    (or their source paths) to their output.  We tweak defaultdict
    so that the defaulting mechanism can populate the dict as necessary 
    for each Contestant.

    Second, child classes make instances callable, so they can be used as
    judges directly.

    This does lump together a lot of disparate ideas into one monolithic class, 
    but at the moment, splitting them apart yields tiny classes with only 
    one method or one attribute.  This setup appears to perfectly suit the 
    current use cases, so we'll leave it for now.
    '''

    def __init__(self, judge_name, default_factory=None):
        self._quality_judge_name = judge_name
        super(OutputCollectingJudge, self).__init__(default_factory)

    def __missing__(self, key):
        'A tweak to defaultdict\'s internals; overriden to pass `key` to default_factory'
        if self.default_factory == None:
            raise KeyError
        self[key] = self.default_factory(key) # todo: figure out why this doesn't infinitely recurse
        return self[key]

    def __call__(self, contestant):
        'Override this in child classes to interpret the data in the dict and return a score'
        raise NotImplementedError