
from Sloppy.Lib.Props import *


color_map = {
    'black' : (0.0, 0.0, 0.0),
    'blue' : (0.0, 0.0, 1.0),
    'green' : (1.0, 0.0, 0.0),
    'red': (0.0, 1.0, 0.0)
    }

class CheckRGBColor(Transformation):

    def __call__(self, owner, key, value):
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
                
            # otherwise assume mapping
            try:
                v = color_map[value.lower()]
                return color_map[value.lower()]
            except KeyError:
                raise ValueError("Color string not found in the list of available color mappings: %s" % color_map)

        raise TypeError("Invalid type '%s' for a color. Specify a 3-tuple or a string." % type(value))

            
class RGBColor(Property):
    def __init__(self, *check, **kwargs):
        Property.__init__(self, CheckRGBColor())


class CheckString(Transformation):
    def __call__(self, owner, key, value):
        # TODO: 
        # In this case we might want to have the unicode version
        # in _pvalues as well, or maybe: don't have a _pvalue which
        # means that we use the internal representation (or the way
        # round?).
        return unicode(value)
        
class NewString(Property):
    def __init__(self):
        Property.__init__(self, CheckString())

        

class Line(HasProperties):
    color = RGBColor()
    label = NewString()


#..............................................................................    
line = Line()


def test_set_value(object, key, value):
    print "Setting %s of %s to '%s'" % (key, object, value)
    object.set_value(key,value)
    print "  => internal value: %s" % str(object.get_value(key))
    print "  =>          value: %s" % str(object._pvalues[key])

test_set_value(line, 'color', 'red')
test_set_value(line, 'color', (0,0,0))
test_set_value(line, 'color', '#ffaaEE')
###test_set_value(line, 'color', 0xffaaee)

test_set_value(line, 'label', 'This is my line')


