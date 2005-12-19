

" Common Properties. "


from props import *


__all__ = ["Integer", "Float", "Keyword", "String", "Boolean", "Unicode"]


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
