'Integrate the "tabnanny" module as a quality judge'

import quality.dec

import StringIO
import sys
import tabnanny

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

class TabnannyJudge(object):
    '''
    Attributes:
    * `results` - a dict mapping filenames to either bools; True means the file has identation problems
    '''
    def __init__(self):
        self.results = {}

    def run_tabnanny(self, src_file):
        'Validate a file and store the result in self.results'
        output_buffer = StringIO.StringIO()
        with PatchContext(sys, 'stdout', output_buffer):
            tabnanny.check(src_file)
        
        # if tabnanny wrote some output, then an error was detected
        self.results[src_file] = 1 if output_buffer.len > 0 else 0
            
    @quality.dec.judge('tabnanny')
    def judge_tabnanny(self, contestant, coverage_file=None):
        '''
        Return 1 is in a file with indentation errors, or 0 otherwise.

        Tabnanny works on a per-file basis; because indentation analysis is 
        context-sensitive, it's impossible to validate individual Contestants
        (functions or classes).  Therefore, every Contestant in a module receives
        the same score.
        '''
        if contestant.src_file not in self.results:
            self.run_tabnanny(contestant.src_file)

        return self.results[contestant.src_file]