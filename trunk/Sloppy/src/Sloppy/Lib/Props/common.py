

" Common Properties. "


from main import *


__all__ = ["Integer", "Float", "Keyword", "String", "Boolean", "Unicode",
           "IntegerRange", "FloatRange", "Instance"]


class String(Property):
    def __init__(self, default="", **kwargs):
        Property.__init__(self, VString(), default=default, **kwargs)

class Boolean(Property):
    def __init__(self, default=False, **kwargs):
        Property.__init__(self, VBoolean(), default=default, **kwargs)

class Keyword(Property):
    def __init__(self, default="", **kwargs):
        Property.__init__(self, VRegexp('^[\-\.\s\w]*$'), default=default, **kwargs)

class Unicode(Property):
    def __init__(self, default="", **kwargs):
        Property.__init__(self, VUnicode(), default=default, **kwargs)

class Integer(Property):
    def __init__(self, default=0, **kwargs):
        Property.__init__(self, VInteger(), default=default, **kwargs)

class Float(Property):
    def __init__(self, default=0.0, **kwargs):
        Property.__init__(self, VFloat(), default=default, **kwargs)
        
class IntegerRange(Property):
    def __init__(self, min=None, max=None, default=Undefined, **kwargs):
        if default is Undefined:
            if min is not None:
                default = min
            elif max is not None:
                default = max
        Property.__init__(self, RequireAll(VInteger(), VRange(min,max)),
                          default=default, **kwargs)

class FloatRange(Property):
    def __init__(self, min=None, max=None, default=Undefined, **kwargs):
        if default is Undefined:
            if min is not None:
                default = min
            elif max is not None:
                default = max            
        Property.__init__(self, RequireAll(VFloat(), VRange(min,max)),
                          default=default, **kwargs)

class Instance(Property):
    def __init__(self, type, default=Undefined, **kwargs):
        Property.__init__(self, VInstance(type), default=default, **kwargs)
        
