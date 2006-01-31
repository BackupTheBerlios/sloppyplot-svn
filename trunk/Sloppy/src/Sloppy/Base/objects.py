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
    'line.marker_color' : ['black', 'red', 'blue', 'green'],    
    'position_system' : ['data', 'graph', 'screen', 'display'],
    'position_valign' : ['center', 'top','bottom'],
    'position_halign' : ['center', 'left','right'],
    'line.marker' : [
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
    
}




#------------------------------------------------------------------------------
# BASE OBJECTS
# 

    
class TextLabel(HasProperties):
    " Single text label. "
    text = Unicode('', blurb="Displayed Text")
    x = Float(0.0, blurb="X-Position")
    y = Float(0.0, blurb="Y-Position")
    system = VP(PV['position_system'], blurb="Coordinate System")
    valign = VP(PV['position_valign'], blurb="Vertical Alignment")
    halign = VP(PV['position_halign'], blurb="Horizontal Aligment")    


class Axis(HasProperties):
    " A single axis for a plot. "
    label = VP(Unicode, None, blurb='Label')

    start = VP(Float, None, default=None, blurb='Start')
    end = VP(Float, None, default=None, blurb='End')

    scale = VP(PV['axis.scale'])
    format = String('', blurb='Format')

    
        
class Line(HasProperties):
    " A single line or collection of points in a Plot. "
    label = VP(Unicode, None)
    visible = Boolean(True)
    
    style = VP([None] + PV['line.style'])
    width = VP(FloatRange(0, 10), None, default=None)
    color = VP([None] + PV['line.color'])

    marker = VP([None] + PV['line.marker'])
    marker_color = VP([None] + PV['line.marker_color'])
    marker_size = FloatRange(0,None,default=1)        
    
    # source stuff (soon deprecated)
    cx = VP(IntegerRange(0,None), None, default=0, blurb="x")
    cy = VP(IntegerRange(0,None), None, default=1, blurb="y")
    row_first = VP(IntegerRange(0,None), None, default=None, blurb="first row")
    row_last = VP(IntegerRange(0,None), None, default=None, blurb="last row")

    #value_range = VP(transform=str)    
    cxerr = VP(IntegerRange(0,None), None)
    cyerr = VP(IntegerRange(0,None), None)

    source = VP(VInstance(Dataset), None, default=None)    



class Legend(HasProperties):
    " Plot legend. "
    label = VP(Unicode, None, doc='Legend Label')
    visible = Boolean(True)
    border = Boolean(False)
    position = VP(PV['legend.position'])   
    x = FloatRange(0.0, 1.0, default=0.7)
    y = FloatRange(0.0, 1.0, default=0.0)



class Layer(HasProperties, HasSignals):
    type = VP(PV['layer.type'])
    title = VP(Unicode, None, blurb="Title")
    lines = List(Line, blurb="Lines")
    grid = Boolean(default=False, blurb="Grid", doc="Display a grid")
    visible = Boolean(True, blurb="Visible")
    legend = Instance(Legend, on_default=lambda: Legend())

    x = FloatRange(0.0, 1.0, default=0.11)
    y = FloatRange(0.0, 1.0, default=0.125)
    width = FloatRange(0.0, 1.0, default=0.775)
    height = FloatRange(0.0, 1.0, default=0.79)

    group_style = Group(Line.style,
                        mode=MODE_CONSTANT,                            
                        constant_value=PV['line.style'][0],
                        allow_override=True)

    group_marker = Group(Line.marker,
                         mode=MODE_CONSTANT,                             
                         constant_value=PV['line.marker'][0],
                         allow_override=True)

    group_width = Group(Line.width,
                        mode=MODE_CONSTANT,
                        constant_value=1.0,
                        allow_override=True)

    group_color = Group(Line.color,
                        mode=MODE_CYCLE,
                        cycle_list=PV['line.color'],
                        allow_override=True)

    group_marker_color = Group(Line.marker_color,
                               mode=MODE_CONSTANT,
                               constant_value=PV['line.marker_color'][0],
                               allow_override=True)
    
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

    title = VP(Unicode, None, blurb="Title")
    comment = Unicode(blurb="Comment")
    
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
    


