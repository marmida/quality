'pylint evaluation as a judge'

from __future__ import absolute_import

import quality.liason
import quality.dec

import pylint.lint
from pylint.reporters.text import ParseableTextReporter
import re
import StringIO
import sys
import traceback
import warnings

SCORE_MAP = {
    'R': 1, # refactor
    'C': 1, # convention
    'W': 2, # warning - stylistic problems, minor bugs
    'E': 10, # errors - "most probably a bug"
    'F': 0, # fatal errors that stopped pylint processing - not necessarily a bug in source?
}

MESSAGE_REGEX = re.compile(r'^[^:]+:([\d]+): \[([\w]).*$')

def run_pylint(src_file):
    '''
    Dispatch to pylint, once per module
    
    We need to fiddle with stderr because pylint insists on repeatedly telling
    us about its lack of a configuration file.  We don't want to suppress all 
    of stderr, so we instead selectively target offending messages.
    '''
    buf = StringIO.StringIO()
    try:
        with quality.liason.PatchContext(sys, 'stderr', quality.liason.FilteredFileProxy(sys.stderr, 'No config file found, using default configuration')):
            pylint.lint.Run(['-r', 'n', src_file], reporter=ParseableTextReporter(output=buf), exit=False)
    except Exception:
        warnings.warn('pylint encountered a fatal error attempting to process the file: %s\n%s' % (src_file, traceback.format_exc()))

    buf.seek(0)
    return buf
    
class LintJudge(quality.liason.OutputCollectingJudge):
    def __init__(self):
        super(LintJudge, self).__init__('lint', run_pylint)

    def msg_types(self, contestant):
        'Yield message categories for each message recorded for this Contestant'
        buf = self[contestant.src_file]
        buf.seek(0) # rewind in case previous runs have exhausted
        for line in buf:
            matches = MESSAGE_REGEX.match(line)
            if matches:
                line, category = matches.group(1, 2)
                if int(line) in contestant.linenums:
                    yield category

    def __call__(self, contestant):
        '''
        pylint runs on a per-module basis, like tabnanny.  However, it reports
        line numbers with each message, so we can associate individual messages
        with Contestants.

        Scan through the output, looking for lines that are within the requested
        contestant.  Return the sum of the message weights, which are determined
        by the category of each message.
        '''
        return sum(SCORE_MAP[category] for category in self.msg_types(contestant))