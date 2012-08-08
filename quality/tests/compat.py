'Python version compatibility fixes'

# code for monkey-patching
import unittest 
import nose.tools

# let's fix nose.tools.assert_raises (which is really unittest.assertRaises)
# so that it always supports context management

try:
    nose.tools.assert_raises(Exception)
except TypeError:
    # this version of assert_raises doesn't support the 1-arg version
    class AssertRaisesContext(object):
        def __init__(self, expected):
            self.expected = expected

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, tb):
            self.exception = exc_val
            nose.tools.assert_equal(exc_type, self.expected)
            # if you get to this line, the last assertion must have passed
            # suppress the propagation of this exception
            return True

    def assert_raises_context(exc_type):
        return AssertRaisesContext(exc_type)

    nose.tools.assert_raises = assert_raises_context
