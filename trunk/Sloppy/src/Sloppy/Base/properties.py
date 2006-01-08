" Additional, SloppyPlot-specific Properties. "

from Sloppy.Lib.Props import *

__all__ = ["VRGBColor", "RGBColor", "MarkerStyle", "BooleanOrNone"]

    
class VRGBColor(Validator):
    
    def check(self, value):
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
        'g' : (1.0, 0.0, 0.0),
        'green' : (1.0, 0.0, 0.0),
        #
        'black' : (0.0, 0.0, 0.0),
        #
        'b' : (0.0, 0.0, 1.0),
        'blue' : (0.0, 0.0, 1.0),
        #
        'r' : (0.0, 1.0, 0.0),
        'red': (0.0, 1.0, 0.0)
        }
    
    def __init__(self, default=Undefined, **kwargs):
        VP.__init__(self, VRGBColor(), VMap(self.color_map),
                          default=default, **kwargs)                    


#------------------------------------------------------------------------------
# MarkerStyle

class MarkerStyle(VP):

    permitted_values = [
        "None",
        "points",
        "pixels",
        "circle symbols",
        "triangle up symbols",
        "triangle down symbols",
        "triangle left symbols",
        "triangle right symbols",
        "square symbols",
        "plus symbols",
        "cross symbols",
        "diamond symbols",
        "thin diamond symbols",
        "tripod down symbols",
        "tripod up symbols",
        "tripod left symbols",
        "tripod right symbols",
        "hexagon symbols",
        "rotated hexagon symbols",
        "pentagon symbols",
        "vertical line symbols",
        "horizontal line symbols"
        "steps"]
    
    def __init__(self, **kwargs):
        VP.__init__(self, self.permitted_values, **kwargs)

    



#------------------------------------------------------------------------------

class BooleanOrNone(VP):
    def __init__(self, default=Undefined, **kwargs):
        VP.__init__(self, (VBoolean(),None), **kwargs)
        
    
