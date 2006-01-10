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


"""
Collection of all basic data objects used for SloppyPlot.
"""
 
from Sloppy.Base.dataset import Dataset
from Sloppy.Base.properties import *

from Sloppy.Lib.Signals import HasSignals
from Sloppy.Lib.Undo import udict
from Sloppy.Lib.Props import *

from properties import *
from groups import *


# ----------------------------------------------------------------------
#  PERMITTED VALUES
#

PV = {
#    'PointType': ['circle','square'],
    'legend.position': ['best', 'center', 'lower left', 'center right', 'upper left',
                        'center left', 'upper right', 'lower right',
                        'upper center', 'lower center',
                        'outside', 'at position'],
    'axis.scale': ['linear','log'],
    'line.style' : ["solid","dashed","dash-dot","dotted","steps","None"],
    'layer.type' : ['line2d', 'contour'],

    'line.color' : ['green', 'red', 'blue', 'black'],
    'line.marker_color' : ['green', 'red', 'blue', 'black'],
    
    }

MAP = {

'position_system' : {'data' : 0, 'graph': 1, 'screen': 2, 'display': 3},
'position_valign' : {'center':0, 'top':1, 'bottom':2},
'position_halign' : {'center':0, 'left':1, 'right': 2},

'line.marker': {
    "None" : None,
    "points" : 0,
    "pixels" : 1,
    "circle symbols" : 2,
    "triangle up symbols" : 3,
    "triangle down symbols" : 4,
    "triangle left symbols" : 5,
    "triangle right symbols" : 6,
    "square symbols" : 7,
    "plus symbols" : 8,
    "cross symbols" : 9,
    "diamond symbols" : 10,
    "thin diamond symbols" : 11,
    "tripod down symbols" : 12,
    "tripod up symbols" : 13,
    "tripod left symbols" : 14,
    "tripod right symbols" : 15,
    "hexagon symbols" : 16,
    "rotated hexagon symbols" : 17,
    "pentagon symbols" : 18,
    "vertical line symbols" : 19,
    "horizontal line symbols" : 20,
    "steps" : 21
    },

}




#------------------------------------------------------------------------------
# BASE OBJECTS
#

                    
class TextLabel(HasProperties):
    " Single text label. "
    text = Unicode('', blurb="Displayed Text")
    x = Float(0.0, blurb="X-Position")
    y = Float(0.0, blurb="Y-Position")
    system = VP(MAP['position_system'],
                      blurb="Coordinate System")
    valign = VP(MAP['position_valign'],
                      blurb="Vertical Alignment")
    halign = VP(MAP['position_halign'],
                      blurb="Horizontal Aligment")
    


class Axis(HasProperties):
    " A single axis for a plot. "
    label = Unicode('', blurb='Label')
    start = VP(Float, None, default=None, blurb='Start')
    end = VP(Float, None, default=None, blurb='End')

    scale = VP(PV['axis.scale'])
    format = String('', blurb='Format')

    
        
class Line(HasProperties):
    " A single line or collection of points in a Plot. "
    label = Unicode()
    visible = Boolean(True)
    
    style = VP(PV['line.style'])    
    width = FloatRange(0,10, default=1)
    color = RGBColor('black')

    marker = MarkerStyle()
    marker_color = RGBColor('black')
    marker_size = FloatRange(0,None,default=1)        
    
    # source stuff (soon deprecated)
    cx = VP(Integer, VRange(0,None), None, default=0, blurb="x-column")
    cy = VP(Integer, VRange(0,None), None, default=1, blurb="y-column")
    row_first = VP(Integer, VRange(0,None), None, default=None)
    row_last = VP(Integer, VRange(0,None), None, default=None)
    #value_range = VP(transform=str)    
    cxerr = VP(Integer, VRange(0,None), None)
    cyerr = VP(Integer, VRange(0,None), None)
    source = Instance(Dataset)

    def source_to_string(self):

        source = '"%s"' % source.key

        if cx is Undefined and cy is Undefined:
            using = None
        else:
            using = 'using %s:%s' % (cx or '*', cy or '*')

        if row_first is Undefined and row_last is Undefined:
            rows = None
        else:
            rows = 'rows %s:%s' % (row_first or '*', row_last or '*')
            
        return ' '.join((item for item in [source,using,rows] if item is not None))


    def source_from_string(self, string):
        # using regular expressions to parse the string
        # TODO: this does not work yet
        regexp = '(?P<source>\".*\"|[^ ]+)(\s+using\s+(?P<using>.+))?(\s+rows\s+(?P<rows>.+))?'
        
        



class Legend(HasProperties):
    " Plot legend. "
    label = Unicode(doc='Legend Label')
    visible = Boolean(True)
    border = Boolean(False)
    position = VP(PV['legend.position'])   
    x = FloatRange(0.0, 1.0, default=0.7)
    y = FloatRange(0.0, 1.0, default=0.0)



class Layer(HasProperties, HasSignals):
    type = VP(PV['layer.type'])
    title = Unicode(blurb="Title")
    lines = List(Line, blurb="Lines")
    grid = Boolean(default=False, blurb="Grid", doc="Display a grid")
    visible = Boolean(True, blurb="Visible")
    legend = Instance(Legend, on_default=lambda: Legend())

    x = FloatRange(0.0, 1.0, default=0.11)
    y = FloatRange(0.0, 1.0, default=0.125)
    width = FloatRange(0.0, 1.0, default=0.775)
    height = FloatRange(0.0, 1.0, default=0.79)

    groups = List(Group)
    labels = List(TextLabel)

    # axes
    xaxis = Instance(Axis, on_default=lambda: Axis())
    yaxis = Instance(Axis, on_default=lambda: Axis())
    
    def get_axes(self):
        return {'x':self.xaxis, 'y':self.yaxis}
    axes = property(get_axes)

    def __init__(self, **kwargs):
        HasProperties.__init__(self, **kwargs)

        HasSignals.__init__(self)
        self.sig_register('notify')
        self.sig_register('notify::labels')
        

class View(HasProperties):
    start = Float(blurb='Start')
    end = Float(blurb='End')
    

class Plot(HasProperties, HasSignals):
    key = Keyword(blurb="Key")

    title = Unicode(blurb="Title")
    comment = Unicode(blurb="Comment")
    
    legend = Instance(Legend)
    lines = List(Line)
    labels = List(TextLabel)
    layers = List(Layer, blurb="Layers")

    views = List(View, blurb="Views")

#     # might be used to notify the user that this
#     # has been edited, e.g. by displaying a star
#     # in a treeview.
#     edit_mark = pBoolean()
    

    def __init__(self, *args, **kwargs):
        HasProperties.__init__(self, *args, **kwargs)

        HasSignals.__init__(self)
        self.sig_register("closed")
        self.sig_register("changed")
        
#     #----------------------------------------------------------------------
    
    def close(self):
        self.sig_emit('closed')        

    def detach(self):
        self.sig_emit('closed')        
    


#------------------------------------------------------------------------------
# Factory Methods
#

def new_lineplot2d(**kwargs):
    """
    Create a one-layer line plot with the given keyword arguments.
    Arguments that do not match a Plot property are passed on to
    the Layer.
    """

    plot = Plot()
    
    # pass only those keywords to the plot that are meaningful
    plot_kwargs = dict()
    for key in plot.get_props().keys():
        if kwargs.has_key(key):
            plot_kwargs[key] = kwargs.pop(key)
    plot.set_values(**plot_kwargs)

    # ...and then create the appropriate layer, assuming
    # that all remaining keyword arguments are meant for the layer
    kwargs.update( {'type' : 'line2d'} )
    plot.layers = [Layer(**kwargs)]
    
    return plot
    


