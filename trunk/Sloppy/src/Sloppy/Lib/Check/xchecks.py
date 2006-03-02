# This file is part of SloppyPlot, a scientific plotting tool.
# Copyright (C) 2005 Niklas Volbers
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# $HeadURL$
# $Id$


""" Extended, not so commonly needed Check objects. """


from checks import *


class RGBColor(Check):

    colors = {'black': 0x000000,
              'red': 0xFF0000,
              'green': 0x00FF00,
              'blue': 0x0000FF,
              'lightgreen':0x76F476
              }
    
    def check(self, value):
        """
        A color can be defined
         (1) as a verbose string ('black', 'blue', ...)
         (2) as a 3-tuple (r,g,b) where each value is a floating
             point number in between 0 and 1
         (3) as a 3-digit hex code (#rgb)
         (4) as a 6-digit hex code (#rrggbb)
         (5) as an integer (=> no conversion)

        Internally it is stored as a 24-bit number (corresponding to 4).
        """

        if isinstance(value, int):
            return value
        
        if isinstance(value, basestring):
            # string starts with '#' => hex color code
            if value.startswith('#'):
                if len(value) == 4 or len(value) == 7:
                    return int(value[1:], 16)
                raise ValueError("not a valid color code")
                    

            # a string w/o a '#' as first letter => a color name                
            else:
                key = value.lower()
                if self.colors.has_key(key):
                    return self.colors[key]
                raise ValueError("not a valid color name")

        if isinstance(value, (tuple,list)):
            # a 3-tuple => (r,g,b)
            if len(value) == 3:
                base = 1
                color = 0
                for c in value:
                    if 0.0 <= c <= 1.0:
                        color+=c*255
                        base*=16
                    else:
                        raise ValueError("all components of the (r,g,b) color tuple must be in between 0 and 1.0")
                return color
            
            raise ValueError("r,g,b tuple has the wrong length")

        raise ValueError("unknown color format")

    def as_color_tuple(self, value):
        # this gives r,g,b as values from 0x00 to 0xff
        return [hex(c) for c in (value and 0xff0000,
                                 value and 0x00ff00,
                                 value and 0x0000ff)]
