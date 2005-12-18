

" Common Properties. "


from props import *


__all__ = ["Integer", "Float", "Keyword", "String",
           "Boolean", "Unicode",
           #
           "pInteger", "pFloat", "pKeyword", "pString",
           "pBoolean", "pUnicode"
           ]



class Boolean(Prop):
    def __init__(self, **kwargs):
        Prop.__init__(self, CoerceBool(), **kwargs)

    
class CoerceBool(Transformation):

    def __init__(self):
        pass

    def __call__(self, owner, key, value):
        if value is None:
            return None
        else:
            if isinstance(value, basestring):
                if "true".find(value.lower()) > -1:
                    return True
                elif "false".find(value.lower()) > -1:
                    return False
            else:
                return bool(value)

    def get_description(self):
        return "Coerce to Boolean"


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




# for compatibility reasons:
pInteger = Integer
pUnicode = Unicode
pString = String
pKeyword = Keyword
pFloat = Float
pBoolean = Boolean

