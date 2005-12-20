

" Common Properties. "


from props import *


__all__ = ["Integer", "Float", "Keyword", "String", "Boolean",
           "Unicode", "List", "Dictionary"]


class String(Property):
    def __init__(self, *validators, **kwargs):
        Property.__init__(self, *validators + (VString(),), **kwargs)

class Boolean(Property):
    def __init__(self, *validators, **kwargs):
        Property.__init__(self, *validators + (VBoolean(),), **kwargs)

class Keyword(Property):
    def __init__(self, *validators, **kwargs):
        Property.__init__(self, *validators + (VRegexp('^[\-\.\s\w]*$'),), **kwargs)

class Unicode(Property):
    def __init__(self, *validators, **kwargs):
        Property.__init__(self, *validators + (VUnicode(),), **kwargs)

class Integer(Property):
    def __init__(self, *validators, **kwargs):
        Property.__init__(self, *validators + (VInteger(),), **kwargs)

class Float(Property):
    def __init__(self, *validators, **kwargs):
        Property.__init__(self, *validators + (VFloat(),), **kwargs)

class List(Property):
    def __init__(self, *validators, **kwargs):
        if len(validators) == 0:
            Property.__init__(self, VList(), **kwargs)
        elif len(validators) == 1:            
            default = validators[0]
            Property.__init__(self, default, VList(), **kwargs)
        else:
            default = validators[0]
            Property.__init__(self, default, VList(*validators[1:]), **kwargs)


class Dictionary(Property):
    def __init__(self, *validators, **kwargs):
        if len(validators) == 0:
            Property.__init__(self, VDictionary(), **kwargs)
        elif len(validators) == 1:            
            default = validators[0]
            Property.__init__(self, default, VDictionary(), **kwargs)
        else:
            default = validators[0]
            Property.__init__(self, default, VDictionary(*validators[1:]), **kwargs)
