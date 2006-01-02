

" Common Properties. "


from main import *


__all__ = ["Integer", "Float", "Keyword", "String", "Boolean", "Unicode",
           "IntegerRange", "FloatRange", "Instance"]


class String(Property):
    def __init__(self, default=Undefined, **kwargs):
        Property.__init__(self, VString(),
                          default=default, **kwargs)

class Boolean(Property):
    def __init__(self, default=Undefined, **kwargs):
        Property.__init__(self, VBoolean(), **kwargs)

class Keyword(Property):
    def __init__(self, default=Undefined, **kwargs):
        Property.__init__(self, VRegexp('^[\-\.\s\w]*$'), **kwargs)

class Unicode(Property):
    def __init__(self, default=Undefined, **kwargs):
        Property.__init__(self, VUnicode(), **kwargs)

class Integer(Property):
    def __init__(self, default=Undefined, **kwargs):
        Property.__init__(self, VInteger(), **kwargs)

class Float(Property):
    def __init__(self, default=Undefined, **kwargs):
        Property.__init__(self, VFloat(), **kwargs)

        
class IntegerRange(Property):
    def __init__(self, min=None, max=None, **kwargs):
        Property.__init__(self, VInteger(), VRange(min,max), **kwargs)

class FloatRange(Property):
    def __init__(self, min=None, max=None, **kwargs):
        Property.__init__(self, RequireAll(VFloat(), VRange(min,max)), **kwargs)

class Instance(Property):
    def __init__(self, type, **kwargs):
        Property.__init__(self, VInstance(type), **kwargs)
        
