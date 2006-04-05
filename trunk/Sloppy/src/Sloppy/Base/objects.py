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

from Sloppy.Base.tree import Node
from Sloppy.Base.dataset import Dataset

from Sloppy.Lib.Signals import *
from Sloppy.Lib.Undo import udict
from Sloppy.Lib.Check import *

from groups import Group, MODE_CONSTANT, MODE_CYCLE

from Sloppy.Base.baseobj import BaseObject as SPObject



# ----------------------------------------------------------------------
#  PERMITTED VALUES
#

PV = {
    'legend.position': ['best', 'center', 'lower left', 'center right', 'upper left',
                        'center left', 'upper right', 'lower right',
                        'upper center', 'lower center',
                        'outside', 'at position'],
    'axis.scale': ['linear','log'],
    'line.style' : ["solid","dashed","dash-dot","dotted","steps", "None"],
    'layer.type' : ['line2d', 'contour'],

    'line.color' : ['black', 'blue', 'red', 'green', 'cyan', 'magenta', 'yellow'],
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
#                                   BASE OBJECTS
#------------------------------------------------------------------------------

class TextLabel(SPObject):
    " Single text label. "
    text = Unicode(blurb="Displayed Text")
    x = Float(blurb="X-Position")
    y = Float(blurb="Y-Position")
    system = Choice(PV['position_system'], blurb="Coordinate System")
    valign = Choice(PV['position_valign'], blurb="Vertical Alignment")
    halign = Choice(PV['position_halign'], blurb="Horizontal Aligment")    


class Axis(SPObject):
    " A single axis for a plot. "
    label = Unicode(blurb='Label')
    start = Float(init=None, blurb='Start')
    end = Float(init=None, blurb='End')    
    scale = Choice(PV['axis.scale'])
    format = String(blurb='Format')

    
        
class Line(SPObject):
    " A single line or collection of points in a Plot. "
    label = Unicode()
    visible = Boolean(init=True, required=True)
    
    style = Choice([None] + PV['line.style'])
    width = Float(min=0, max=10, init=None)
    color = Choice([None] + PV['line.color'])

    marker = Choice([None] + PV['line.marker'])
    marker_color = Choice([None] + PV['line.marker_color'])
    marker_size = Float(min=0,max=None,init=1)        
    
    # source stuff (soon deprecated)
    cx = Integer(min=0,max=None, init=0, blurb="x")
    cy = Integer(min=0,max=None, init=1, blurb="y")
    row_first = Integer(min=0,max=None,init=None, blurb="first row")
    row_last = Integer(min=0,max=None,init=None, blurb="last row")

    #value_range = VP(transform=str)    
    cxerr = Integer(min=0,max=None)
    cyerr = Integer(min=0,max=None)

    source = Instance(Dataset)

    def get_source(self):
        if self.source is None:
            raise RuntimeError("No data available")
        self.source.get_array() # ensure that data is loaded               
        return self.source

    def get_x(self):
        return self.get_source().get_column(self.cx)
    
    def get_y(self):
        return self.get_source().get_column(self.cy)

    def get_xy(self):
        s = self.get_source()
        return (s.get_column(self.cx), s.get_column(self.cy))

    def get_description(self):
        if isinstance(self.source, Dataset):
            source = "[%s - %s:%s]" % (self.source.key, self.cx, self.cy)
        else:
            source = "[-]"
        return "%s %s" % (self.label or "Line", source)


class Legend(SPObject):
    " Plot legend. "
    label = Unicode(doc='Legend Label')
    visible = Boolean(init=True, required=True)
    border = Boolean(init=False, required=True)
    position = Choice(PV['legend.position'])
    x = Float(min=0.0, max=1.0, init=0.7)
    y = Float(min=0.0, max=1.0, init=0.0)



class Layer(SPObject):
    type = Choice(PV['layer.type'])
    title = Unicode(init=None, blurb="Title")
    lines = List(Instance(Line), blurb="Lines")
    grid = Boolean(init=False, required=True, blurb="Grid", doc="Display a grid")
    visible = Boolean(init=True, required=True, blurb="Visible")
    legend = Instance(Legend, on_init=lambda o,k: Legend())

    x = Float(min=0.0, max=1.0, init=0.11)
    y = Float(min=0.0, max=1.0, init=0.125)
    width = Float(min=0.0, max=1.0, init=0.775)
    height = Float(min=0.0, max=1.0, init=0.79)

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
    
    labels = List(Instance(TextLabel))

    # axes
    #xaxis = Instance(Axis, on_init=lambda o,k: Axis())
    #yaxis = Instance(Axis, on_init=lambda o,k: Axis())
    
    #def get_axes(self):
    #    return {'x':self.xaxis, 'y':self.yaxis}
    #axes = property(get_axes)

    axes = Dict(Axis, on_init=lambda o,k: {'x':Axis(), 'y':Axis()})

    def get_xaxis(self): return self.axes['x']
    def get_yaxis(self): return self.axes['y']
    def set_xaxis(self, axis): self.axes['x'] = axis
    def set_yaxis(self, axis): self.axes['y'] = axis    
    xaxis = property(get_xaxis, set_xaxis)
    yaxis = property(get_yaxis, set_yaxis)


    def get_description(self):        
        return "Layer %s" % (self.title or "")

        

class View(SPObject):
    start = Float(blurb='Start')
    end = Float(blurb='End')
    


###############################################################################


class Plot(Node, SPObject):

    key = Keyword(blurb="Key") # TODO: remove this!
    
    title = Unicode(init=None, blurb="Title")
    comment = Unicode(init=None, blurb="Comment")
    
    labels = List(Instance(TextLabel))
    layers = List(Instance(Layer), blurb="Layers")

    views = List(Instance(View), blurb="Views")   

    
    def __init__(self, *args, **kwargs):
        SPObject.__init__(self, *args, **kwargs)
        Node.__init__(self)

        self.sig_register("closed")
        self.sig_register("changed")

       
#     #----------------------------------------------------------------------
    
    def close(self):
        self.sig_emit('closed')        

    def detach(self):
        self.sig_emit('closed')        
    


