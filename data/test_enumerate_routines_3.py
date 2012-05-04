'''
test excluding source from other modules;
this module defines classes which inherit from those in other modules
'''

import test_enumerate_routines_1

class Child(test_enumerate_routines_1.SomeClass):
    pass

class Child2(test_enumerate_routines_1.SomeClass):
    def another_function(self):
        pass