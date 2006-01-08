
from Sloppy.Lib.Props import *

import re

#------------------------------------------------------------------------------
class VRGBColor(Validator):
    
    def check(self, owner, key, value):
        if isinstance(value, (list,tuple)):
            # assume 3-tuple (red,green,blue)
            if len(value) == 3:
                # mapped value = tuple(value)
                # unmapped value = value
                
                return tuple(value)
            else:
                raise ValueError("Color tuple must be a 3-tuple (RGB).")

        if isinstance(value, basestring):
            # if string starts with '#', then we expect a hex color code
            if value.startswith('#'):
                try:
                    # unmapped value = value
                    # mapped value...
                    return [int(c, 16)/255. for c in (value[1:2], value[3:4], value[5:6])]
                except:
                    raise ValueError("Hex color code must be six digits long and must be 0-9,A-F only.")                

        raise TypeError("a 3-tuple or a string")

    is_mapping = True

    
class RGBColor(VP):
    color_map = {
        'black' : (0.0, 0.0, 0.0),
        'blue' : (0.0, 0.0, 1.0),
        'green' : (1.0, 0.0, 0.0),
        'red': (0.0, 1.0, 0.0)
        }
    
    def __init__(self, default=Undefined, **kwargs):
        VP.__init__(self, VRGBColor(),VMap(self.color_map),
                          default=default, **kwargs)                    
#------------------------------------------------------------------------------


class MySubclass:
    def __init__(self):
        print "Subclass initialized."
        
class Line(HasProperties):
    color = RGBColor('black')
    label = String()
    is_visible = Boolean(True)
    keyword = Keyword()
    comment = Unicode()
    width = Integer(2)
    length = Float(default=4)

    style = VP({'none':None,'solid':1,'dashed':2})
    colors = List(color) 
    history = Dictionary(keyword)

    myline = Instance(MySubclass, on_default=lambda: MySubclass())
    
#..............................................................................    
line = Line()
#print "default values:", line.get_values()
print line.myline

def test_set_value(object, key, value):
    print "Setting %s of %s to '%s'" % (key, object, value)
    object.set_value(key,value)
    print "  => mapped  value: %s" % str(object.get_mvalue(key))
    print "  => visible value : %s" % str(object.get_value(key))


#------------------------------------------------------------------------------
raise SystemExit
#------------------------------------------------------------------------------
test_set_value(line, 'color', 'red')
#test_set_value(line, 'color', None)
test_set_value(line, 'color', (0.0,0,0))
test_set_value(line, 'color', '#ffaaEE')
#test_set_value(line, 'color', 42)

test_set_value(line, 'label', 'This is my line')
test_set_value(line, 'label', 42.0)

test_set_value(line, 'is_visible', True)
test_set_value(line, 'is_visible', False)
test_set_value(line, 'is_visible', 'false')

#test_set_value(line, 'is_visible', None)


test_set_value(line, 'keyword', 'Niki')

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
print line.get_mvalue('colors')
print line.colors

#line.colors = 'Niki'
#line.colors = ['reda']

line.colors[0] = 'red'
test_set_value(line, 'width', 3.2)


line.history['1982'] = 'aa'
print line.history

#line.history['1986'] = 41
#print line.history
