

" Common Properties. "


from main import *
from vprops import *


__all__ = ["Integer", "Float", "Keyword", "String", "Boolean", "Unicode",
           "IntegerRange", "FloatRange", "Instance", "List", "Dictionary"]


class String(VP):
    def __init__(self, default="", **kwargs):
        VP.__init__(self, VString(), default=default, **kwargs)

class Boolean(VP):
    def __init__(self, default=False, **kwargs):
        VP.__init__(self, VBoolean(), default=default, **kwargs)

class Keyword(VP):
    def __init__(self, default="", **kwargs):
        VP.__init__(self, VRegexp('^[\-\.\s\w]*$'), default=default, **kwargs)

class Unicode(VP):
    def __init__(self, default="", **kwargs):
        VP.__init__(self, VUnicode(), default=default, **kwargs)

class Integer(VP):
    def __init__(self, default=0, **kwargs):
        VP.__init__(self, VInteger(), default=default, **kwargs)

class Float(VP):
    def __init__(self, default=0.0, **kwargs):
        VP.__init__(self, VFloat(), default=default, **kwargs)
        
class IntegerRange(VP):
    def __init__(self, min=None, max=None, default=Undefined, **kwargs):
        if default is Undefined:
            if min is not None:
                default = min
            elif max is not None:
                default = max
        VP.__init__(self, RequireAll(VInteger(), VRange(min,max)),
                          default=default, **kwargs)

class FloatRange(VP):
    def __init__(self, min=None, max=None, default=Undefined, **kwargs):
        if default is Undefined:
            if min is not None:
                default = min
            elif max is not None:
                default = max
        VP.__init__(self, RequireAll(VFloat(), VRange(min,max)),
                          default=default, **kwargs)

class Instance(VP):
    def __init__(self, type, default=Undefined, **kwargs):
        VP.__init__(self, VInstance(type), default=default, **kwargs)


class List(VP):
    def __init__(self, *validators, **kwargs):
        # TODO: maybe I should set the default value
        # after initializing the VP.  After all the
        # ValidatorList default value is useless for the list,
        # isn't it?
        if kwargs.has_key('default') is False:
            kwargs['default'] = []
        VP.__init__(self, VList(*validators), **kwargs)


class Dictionary(VP):
    def __init__(self, *validators, **kwargs):        
        if kwargs.has_key('default') is False:
            kwargs['default'] = {}
        VP.__init__(self, VDictionary(*validators), **kwargs)
        
