
from Sloppy.Lib.Props import *

import re

#------------------------------------------------------------------------------
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

    def is_mapping(self):
        return True

    
class RGBColor(Property):
    color_map = {
        'black' : (0.0, 0.0, 0.0),
        'blue' : (0.0, 0.0, 1.0),
        'green' : (1.0, 0.0, 0.0),
        'red': (0.0, 1.0, 0.0)
        }
    
    def __init__(self, *validators, **kwargs):
        Property.__init__(self,
                             *validators + (VRGBColor(),VMap(self.color_map)),
                             **kwargs)                    
#------------------------------------------------------------------------------


        
class Line(HasProperties):
    color = RGBColor('black', None)
    label = String()
    is_visible = Boolean(True, None)
    keyword = Keyword()
    comment = Unicode()
    width = Integer(2)
    length = Float(4)

    style = Property(None, {'none':None,'solid':1,'dashed':2})

    colors = List([], RGBColor)

#..............................................................................    
line = Line()
print "default values:", line.get_values()


def test_set_value(object, key, value):
    print "Setting %s of %s to '%s'" % (key, object, value)
    object.set_value(key,value)
    print "  => internal value: %s" % str(object.get_ivalue(key))
    print "  => visible value : %s" % str(object.get_value(key))

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

test_set_value(line, 'style', 'solid')
test_set_value(line, 'style', 'dashed')
test_set_value(line, 'style', 1)


line.colors.append( (0,0,0.5) )
print line.colors

#line.colors.append( 'Niklas' ) # FAILS
line.colors.append( 'red' )
print line.colors

line.colors = [ (1,0.2,1) ]
line.colors.append( 'red' )
print line.colors

new_list = line.colors + [(0.5,0.2,0.1)]
line.colors = new_list

print "---"
print line.get_value('colors')
print line.get_ivalue('colors')

