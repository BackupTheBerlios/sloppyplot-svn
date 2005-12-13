

" Common Properties. "


from props import *


__all__ = ["Integer", "Float", "Weakref", "Keyword", "String",
           "Boolean", "Unicode",
           #
           "pInteger", "pFloat", "pWeakref", "pKeyword", "pString",
           "pBoolean", "pUnicode"
           ]



class Boolean(Prop):
    def __init__(self, **kwargs):
        Prop.__init__(self, coerce=CoerceBool(), **kwargs)

class Keyword(Prop):
    def __init__(self, **kwargs):
        Prop.__init__(self, type=basestring, #
                      custom=CheckRegexp('^[\-\.\s\w]*$'), # TODO?
                      **kwargs)

class String(Prop):
    """ Coerce to regular string. """
    def __init__(self, *check, **kwargs):
        Prop.__init__(self, coerce=str, *check, **kwargs)

        
class Unicode(Prop):
    """ Coerce to regular string. """
    def __init__(self, *check, **kwargs):
        Prop.__init__(self, coerce=unicode, *check, **kwargs)
        

class Integer(Prop):
    def __init__(self, *check, **kwargs):
        Prop.__init__(self, coerce=int, *check, **kwargs)


class Float(Prop):
    def __init__(self, *check, **kwargs):
        Prop.__init__(self, coerce=float, *check, **kwargs)

        
class Weakref(Prop):

    def __init__(self, *check, **kwargs):
        Prop.__init__(self, *check, **kwargs)
        
    def meta_attribute(self, key):
        return WeakMetaAttribute(self, key)



# for compatibility reasons:

pWeakref = Weakref
pInteger = Integer
pUnicode = Unicode
pString = String
pKeyword = Keyword
pFloat = Float
pBoolean = Boolean

