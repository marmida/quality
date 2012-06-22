'Integrate the "tabnanny" module as a quality judge'

from __future__ import absolute_import

import quality.liason
import quality.dec

import os
import tabnanny

@quality.liason.capture_output
def run_tabnanny(src_file):
    'Dispatch to tabnanny'
    tabnanny.check(src_file)
    
class TabnannyJudge(quality.liason.OutputCollectingJudge):
    def __init__(self):
        super(TabnannyJudge, self).__init__('tabnanny', run_tabnanny)

    def __call__(self, contestant):
        '''
        Return 1 if the Contestant contains with indentation errors, or 0 otherwise.

        Tabnanny works on a per-file basis; because indentation analysis is 
        context-sensitive, it's impossible to validate individual Contestants
        (functions or classes).  Therefore, every Contestant in a module receives
        the same score.
        '''
        fobj = self[contestant.src_file]
        fobj.seek(0, os.SEEK_END)
        return 1 if fobj.tell() else 0