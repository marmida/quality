'tests for cmdline.py'

from nose.tools import *
import os
import re
import shutil
import tempfile

import quality.cmdline

class TempDir(object):
    '''
    A context manager that, on entrance, creates a temp dir and cds into it.
    On exit, it deletes everything in the temp dir, and restores the original
    CWD.
    '''
    def __enter__(self):
        self.orig_cwd = os.getcwd()
        self.path = tempfile.mkdtemp()
        os.chdir(self.path)
        return self

    def __exit__(self, exc_type, exc_val, tb):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.path)

def _test_find_source_files(path, exclude, include, expected):
    'run one test against find_source_files'
    if include:
        include = [re.compile(i) for i in include]
    if exclude:
        exclude = [re.compile(i) for i in exclude]
    actual = quality.cmdline.find_source_files(path, exclude, include)
    assert_equal(set(expected), set(actual))

def test_find_source_files():
    'find_source_files: correctly enumerates files and respects include and exclude options'
    # it's easier to build a tailored environment in a temp directory than to 
    # mock all the filesystem access functions
    # all generated tests will use the same environment
    with TempDir() as container_dir:
        for i in ['dir_a', 'dir_b/dir_b1', 'dir_b/dir_b2', 'decoy.py']:
            os.makedirs(os.path.join(container_dir.path, i))
        file_paths = [
            'container.py',
            'readme.txt',
            'license',
            'dir_a/a.py',
            'dir_b/b.py',
            'dir_b/dir_b1/b1.py',
            'dir_b/dir_b2/b2.py',
            'decoy.py/decoy.py',
        ]
        for i in file_paths:
            open(os.path.join(container_dir.path, i), 'w').close()

        args_ls = [
            # (path, include, exclude, expected)
            ('.', None, None, ['./container.py', './dir_a/a.py', './dir_b/b.py', './dir_b/dir_b1/b1.py', './dir_b/dir_b2/b2.py', './decoy.py/decoy.py']),
            ('dir_a', None, None, ['dir_a/a.py']),
            # single exclude
            ('.', [r'^\./dir_[^/]/*'], None, ['./container.py', './decoy.py/decoy.py']),
            # multiple excludes
            ('.', [r'a', r'[\d]'], None, ['./decoy.py/decoy.py', './dir_b/b.py']),
            # single include

            # multiple includes

            # given a path to a directory that looks like a file, find the file inside it
            ('decoy.py', None, None, ['decoy.py/decoy.py']),
            # given a path to a single file, return that file
            ('container.py', None, None, ['container.py']),
        ]
        for args in args_ls:
            yield (_test_find_source_files,) + args 

        # error handling tests
        with assert_raises(ValueError) as exception_context:
            quality.cmdline.find_source_files(os.path.join(container_dir.path, 'non-existent-path'))