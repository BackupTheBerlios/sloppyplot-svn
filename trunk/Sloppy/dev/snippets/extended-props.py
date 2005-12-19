
from Sloppy.Lib.Props import *

import re



class Validator:
    pass

class VMap(Validator):

    """ Map the given value according to the dict. """
    
    def __init__(self, adict):
        self.dict = adict
        self.values = adict.values()

    def check(self, owner, key, value):
        try:
            return self.dict[value]
        except KeyError:
            raise ValueError("Could not find value '%s' in the list of mappings '%s'" % (value, self.dict))


class VRGBColor(Validator):
    
    def check(self, owner, key, value):
        if isinstance(value, (list,tuple)):
            # assume 3-tuple (red,green,blue)
            if len(value) == 3:
                return tuple(value)
            else:
                raise ValueError("Color tuple must be a 3-tuple (RGB).")

        if isinstance(value, basestring):
            # if string starts with '#', then we expect a hex color code
            if value.startswith('#'):
                try:
                    return [int(c, 16)/255. for c in (value[1:2], value[3:4], value[5:6])]
                except:
                    raise ValueError("Hex color code must be six digits long and must be 0-9,A-F only.")                

        raise TypeError("a 3-tuple or a string")


class VNone(Validator):

    def check(self, owner, key, value):
        if value is None:
            return None
        raise TypeError("None")


class VBoolean(Validator):

    def check(self, owner, key, value):
        if isinstance(value, bool):
            return bool(value)
        elif isinstance(value, basestring):
            if "true".find(value.lower()) > -1:
                return True
            elif "false".find(value.lower()) > -1:
                return False
        elif isinstance(value, (int,float)):
            return bool(value)

        raise ValueError("Not a valid True/False value.")

class VString(Validator):
    def check(self, owner, key, value):
        return str(value)

class VUnicode(Validator):
    def check(self, owner, key, value):
        return unicode(value)


class VInteger(Validator):
    def check(self, owner, key, value):
        return int(value)

class VFloat(Validator):
    def check(self, owner, key, value):
        return float(value)

class VRegexp(Validator):
    
    """ Check value against a given regular expression. """
    
    def __init__(self, regexp):
        self.regexp=regexp
        self._expression = re.compile(regexp)

    def check(self, owner, key, value):
        match = self._expression.match(value)
        if match is not None:
            return value

        raise ValueError("Value %s does not match the regular expression %s" % (value,self.regexp))


#------------------------------------------------------------------------------

class NewProperty(Property):
    def __init__(self, *validators, **kwargs):
        Property.__init__(self, **kwargs)
        self.validators = []
        
        # first item in validators is actually the default value
        # unless it is a validator instance
        if len(validators) > 0:
            default = validators[0]
            print "Found default value", default
            if not isinstance(default, Validator):
                self.on_reset = lambda o,k: default
                validators = tuple(validators[1:])

        # init validators
        for item in validators:
            if isinstance(item, Validator):
                v = item
            elif item is None:
                v = VNone()
            elif isinstance(item, dict):
                # TODO: 1:1 mapping if there is only a map as validator
                v = VMap(item)
            else:
                raise TypeError("Unknown validator: %s" % item)

            self.validators.append(v)

                                
    def check(self, owner, key, value):
        error = ""
        for validator in self.validators:
            try:
                value = validator.check(owner, key, value)
            except ValueError, msg:
                error += str(msg)
            except TypeError, msg:
                error += str(msg)
            except:
                raise
            else:
                return value

        raise TypeError(error)

    
class RGBColor(NewProperty):
    color_map = {
        'black' : (0.0, 0.0, 0.0),
        'blue' : (0.0, 0.0, 1.0),
        'green' : (1.0, 0.0, 0.0),
        'red': (0.0, 1.0, 0.0)
        }
    
    def __init__(self, *validators, **kwargs):
        NewProperty.__init__(self,
                             *validators + (VRGBColor(),self.color_map),
                             **kwargs)
                    
class NewString(NewProperty):
    def __init__(self, *validators, **kwargs):
        NewProperty.__init__(self, *validators + (VString(),), **kwargs)

class NewBoolean(NewProperty):
    def __init__(self, *validators, **kwargs):
        NewProperty.__init__(self, *validators + (VBoolean(),), **kwargs)

class NewKeyword(NewProperty):
    def __init__(self, *validators, **kwargs):
        NewProperty.__init__(self, *validators + (VRegexp('^[\-\.\s\w]*$'),), **kwargs)

class NewUnicode(NewProperty):
    def __init__(self, *validators, **kwargs):
        NewProperty.__init__(self, *validators + (VUnicode(),), **kwargs)

class NewInteger(NewProperty):
    def __init__(self, *validators, **kwargs):
        NewProperty.__init__(self, *validators + (VInteger(),), **kwargs)

class NewFloat(NewProperty):
    def __init__(self, *validators, **kwargs):
        NewProperty.__init__(self, *validators + (VFloat(),), **kwargs)

        
        
class Line(HasProperties):
    color = RGBColor('black', None)
    label = NewString()
    is_visible = NewBoolean(True, None)
    keyword = NewKeyword()
    comment = NewUnicode()
    width = NewInteger(2)
    length = NewFloat(4)


#..............................................................................    
line = Line()
print "default values:", line.get_values()


def test_set_value(object, key, value):
    print "Setting %s of %s to '%s'" % (key, object, value)
    object.set_value(key,value)
    print "  => internal value: %s" % str(object.get_value(key))
    print "  =>          value: %s" % str(object._pvalues[key])

test_set_value(line, 'color', 'red')
test_set_value(line, 'color', None)
test_set_value(line, 'color', (0,0,0))
test_set_value(line, 'color', '#ffaaEE')
#test_set_value(line, 'color', 42)

test_set_value(line, 'label', 'This is my line')
test_set_value(line, 'label', 42.0)

test_set_value(line, 'is_visible', True)
test_set_value(line, 'is_visible', False)
test_set_value(line, 'is_visible', 'false')

test_set_value(line, 'is_visible', None)


test_set_value(line, 'keyword', 'Niki')
#test_set_value(line, 'keyword', 'Ätzend')
