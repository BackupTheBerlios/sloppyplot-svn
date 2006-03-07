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




# ----------------------------------------------------------------------
#  PERMITTED VALUES
#

PV = {
    'legend.position': ['best', 'center', 'lower left', 'center right', 'upper left',
                        'center left', 'upper right', 'lower right',
                        'upper center', 'lower center',
                        'outside', 'at position'],
    'axis.scale': ['linear','log'],
    'line.style' : ["solid","dashed","dash-dot","dotted","steps","None"],
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




class SPObject(HasChecks, HasSignals):
       
    def __init__(self, **kwargs):
        HasChecks.__init__(self, **kwargs)
        HasSignals.__init__(self)
        
        # set up available Signals       
        self.signals['update'] = Signal()

        # The update::key signals are different for normal attributes
        # and for List/Dict attributes, which have their own on_update
        # method. It is necessary to use new_lambda, because in case of
        #  self._values[key].on_update = lambda ....
        # the lambda would be redefined with each iteration and
        # every List/Dict object would emit the same signal.        
        
        def new_lambda(key):
            return lambda sender, updateinfo: self.sig_emit('update::%s'%key, updateinfo)        

        for key, check in self._checks.iteritems():
            self.signals['update::%s'%key] = Signal()            
            if isinstance(check, (List,Dict)):
                self._values[key].on_update = new_lambda(key)                 

        # trigger Signals on attribute update
        def on_update(sender, key, value):
            self.sig_emit('update', key, value)
            self.sig_emit('update::%s'%key, value)
            # the above form causes a notification message, the above one is quicker.            
            ##sender.signals['update'](sender, key, value)
            ##sender.signals['update::%s'%key](sender, value) # TODO: what about List/Dict?
        self.on_update = on_update



        
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
    visible = Boolean(init=True)
    
    style = Choice([None] + PV['line.style'])
    width = Float(min=0, max=10, init=None)
    color = Choice([None] + PV['line.color'])

    marker = Choice([None] + PV['line.marker'])
    marker_color = Choice([None] + PV['line.marker_color'])
    marker_size = Float(min=0,max=None,init=1)        
    
    # source stuff (soon deprecated)
    cx = Integer(min=0,mqax=None, init=0, blurb="x")
    cy = Integer(min=0,max=None, init=1, blurb="y")
    row_first = Integer(min=0,max=None,init=None, blurb="first row")
    row_last = Integer(min=0,max=None,init=None, blurb="last row")

    #value_range = VP(transform=str)    
    cxerr = Integer(min=0,max=None)
    cyerr = Integer(min=0,max=None)

    source = Instance(Dataset)



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
    grid = Boolean(init=False, blurb="Grid", doc="Display a grid")
    visible = Boolean(init=True, blurb="Visible")
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
    xaxis = Instance(Axis, on_init=lambda o,k: Axis())
    yaxis = Instance(Axis, on_init=lambda o,k: Axis())
    
    def get_axes(self):
        return {'x':self.xaxis, 'y':self.yaxis}
    axes = property(get_axes)

        

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
    


