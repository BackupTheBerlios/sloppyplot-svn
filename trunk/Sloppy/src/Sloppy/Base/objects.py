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
 
from Sloppy.Base.const import PV, DP
from Sloppy.Base.dataset import Dataset
from Sloppy.Base import const


from Sloppy.Lib import Signals
from Sloppy.Lib.Undo import udict
from Sloppy.Lib.Props import *
       
        
map_system = {'data' : 0, 'graph': 1, 'screen': 2, 'display': 3}
map_valign = {'center':0, 'top':1, 'bottom':2}
map_halign = {'center':0, 'left':1, 'right': 2}



#------------------------------------------------------------------------------
# BASE OBJECTS
#

class TextLabel(HasProps):
    " Single text label. "
    text = pUnicode()
    x = pFloat()
    y = pFloat()
    system = pInteger(MapValue(map_system), default=0)
    valign = pInteger(MapValue(map_valign), default=0)
    halign = pInteger(MapValue(map_halign), default=0)
    


class Axis(HasProps):
    " A single axis for a plot. "
    label = pUnicode(blurb='Label')
    start = pFloat(blurb='Start')
    end = pFloat(blurb='End')

    scale = pString(CheckValid(PV['axis.scale']), blurb='Scale')
    format = pString(blurb='Format')


class Line(HasProps):
    " A single line or collection of points in a Plot. "
    label = pUnicode()
    cx = pInteger(CheckBounds(min=0), blurb="x-column")
    cy = pInteger(CheckBounds(min=0), blurb="y-column")
    row_first = pInteger(CheckBounds(min=0))
    row_last = pInteger(CheckBounds(min=0))
    #value_range = Prop(transform=str)    
    cxerr = pInteger(CheckBounds(min=0))
    cyerr = pInteger(CheckBounds(min=0))
    source = Prop(CheckType(Dataset))
    width = pFloat(CheckBounds(min=0, max=10), default=const.default_params['line.width'])
    style = Prop(CheckValid(PV['line.style']))
    marker = Prop(CheckValid(PV['line.marker']))
    color = pString()
    visible = pBoolean()


class Legend(HasProps):
    " Plot legend. "
    label = pUnicode(doc='Legend Label')
    visible = pBoolean()
    border = pBoolean()
    position = Prop(CheckValid(PV['legend.position']))
    x = pFloat(CheckBounds(min=0.0, max=1.0))
    y = pFloat(CheckBounds(min=0.0, max=1.0))


class Layer(HasProps):
    type = pString(CheckValid(PV['layer.type']))
    title = pUnicode(blurb="Title")
    lines = pList(CheckType(Line), blurb="Lines")
    grid = pBoolean(blurb="Grid", doc="Display a grid", default=DP['layer.grid'])
    visible = pBoolean(blurb="Visible", default=DP['layer.visible'])
    legend = Prop(CheckType(Legend), reset=(lambda: Legend()))

    x = pFloat(CheckBounds(min=0.0, max=1.0))
    y = pFloat(CheckBounds(min=0.0, max=1.0))
    width = pFloat(CheckBounds(min=0.0, max=1.0))
    height = pFloat(CheckBounds(min=0.0, max=1.0))

    group_colors = pString(default=const.default_params['layer.group_colors'])
    group_styles = pList(CheckType(str))
    group_markers = pList(CheckType(str))

    labels = pList(CheckType(TextLabel))

    # axes
    xaxis = Prop(CheckType(Axis), reset=(lambda:Axis()))
    yaxis = Prop(CheckType(Axis), reset=(lambda:Axis()))
    
    def get_axes(self):
        return {'x':self.xaxis, 'y':self.yaxis}
    axes = property(get_axes)
    

class View(HasProps):
    start = pFloat(blurb='Start')
    end = pFloat(blurb='End')
    

class Plot(HasProps):
    key = pKeyword(blurb="Key")

    title = pUnicode(blurb="Title")
    comment = pUnicode(blurb="Comment")
    
    legend = Prop(CheckType(Legend))
    lines = pList(CheckType(Line))
    labels = pList(CheckType(TextLabel))
    layers = pList(CheckType(Layer), blurb="Layers")

    views = pList(CheckType(View), blurb="Views")

    # might be used to notify the user that this
    # has been edited, e.g. by displaying a star
    # in a treeview.
    edit_mark = pBoolean()
    

    def __init__(self, *args, **kwargs):
        HasProps.__init__(self, *args, **kwargs)
        self._current_layer = None
        
    #----------------------------------------------------------------------

    def get_current_layer(self):
        """
        Returns the current layer.
        Make sure that the current_layer actually exists.
        If this is not the case, the current_layer attribute is reset.
        """
        if self._current_layer is None:
            return None
        if self._current_layer in self.layers:
            return self._current_layer

        self.set_current_layer(None)
        return None

    def set_current_layer(self, layer):
        """
        Set the current layer.
        The layer must be either None or a Layer instance that is
        contained in self.layers.
        """
        if layer is None or layer in self.layers:
            self._current_layer = layer
            Signals.emit(self, "notify::current_layer", layer)
        else:
            raise ValueError("Layer %s can't be set as current, because it is not part of the Plot!" % layer)

    current_layer = property(get_current_layer, set_current_layer)            
        
    #----------------------------------------------------------------------
    
    def close(self):
        Signals.emit(self, 'closed')

    def detach(self):
        Signals.emit(self, 'closed')
    


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
    


