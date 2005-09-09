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
 
from Sloppy.Base.const import PV
from Sloppy.Base.dataset import Dataset

from Sloppy.Lib import Signals
from Sloppy.Lib.Undo import udict
from Sloppy.Lib.Props import *
       
        

#------------------------------------------------------------------------------
# BASE OBJECTS
#

class Axis(Container):
    " A single axis for a plot. "
    label = StringProp(blurb='Label')
    start = Prop(Coerce(float), blurb='Start')
    end = Prop(Coerce(float), blurb='End')

    scale = Prop(CheckType(str), CheckValid(PV['axis.scale']),
                 blurb='Scale')
    format = Prop(CheckType(str), blurb='Format')


class Line(Container):
    " A single line or collection of points in a Plot. "
    label = StringProp()
    cx = RangeProp(Coerce(int), min=0, blurb="x-column")
    cy = RangeProp(Coerce(int), min=0, blurb="y-column")
    row_first = RangeProp(Coerce(int),min=0)
    row_last = RangeProp(Coerce(int),min=0)
    #value_range = Prop(transform=str)    
    cxerr = RangeProp(Coerce(int), min=0)
    cyerr = RangeProp(Coerce(int), min=0)
    source = Prop(CheckType(Dataset))
    width = RangeProp(Coerce(float), min=0, max=10)
    style = Prop(CheckValid(PV['line.style']))
    marker = Prop(CheckValid(PV['line.marker']))
    color = Prop(Coerce(str))
    visible = BoolProp()


class Legend(Container):
    " Plot legend. "
    label = StringProp(doc='Legend Label')
    visible = BoolProp()
    border = BoolProp()
    position = Prop(CheckType(str), value_list=PV['legend.position'])
    x = RangeProp(Coerce(float), min=0.0, max=1.0)
    y = RangeProp(Coerce(float), min=0.0, max=1.0)


class Layer(Container):
    type = Prop(CheckType(str), value_list=PV['layer.type'])
    title = StringProp(blurb="Title")
    axes = DictProp(CheckType(Axis), blurb="Axes")
    lines = ListProp(CheckType(Line), blurb="Lines")
    grid = BoolProp(blurb="Grid", doc="Display a grid")
    visible = BoolProp(blurb="Visible")
    legend = Prop(CheckType(Legend),
                  reset=Legend)

    x = RangeProp(CheckType(float), min=0.0, max=1.0)
    y = RangeProp(CheckType(float), min=0.0, max=1.0)
    width = RangeProp(CheckType(float), min=0.0, max=1.0)
    height = RangeProp(CheckType(float), min=0.0, max=1.0)    

    group_colors = Prop(CheckType(str))
    group_styles = ListProp(CheckType(str))
    group_markers = ListProp(CheckType(str))

    def request_axis(self, key, undolist=[]):
        if self.axes.has_key(key) is False:            
            udict.setitem( self.axes, key, Axis(), undolist=undolist)
        return self.axes[key]        
    
    
class TextLabel(Container):
    " Single text label. "
    text = StringProp()
    
    x = Prop(Coerce(float))
    y = Prop(Coerce(float))



class View(Container):
    start = Prop(Coerce(float), blurb='Start')
    end = Prop(Coerce(float), blurb='End')
    

class Plot(Container):
    key = KeyProp(blurb="Key")

    title = StringProp(blurb="Title")
    comment = StringProp(blurb="Comment")
    
    legend = Prop(CheckType(Legend))
    lines = ListProp(CheckType(Line))
    labels = ListProp(CheckType(TextLabel))
    layers = ListProp(CheckType(Layer), blurb="Layers")

    views = ListProp(CheckType(View), blurb="Views")

    # might be used to notify the user that this
    # has been edited, e.g. by displaying a star
    # in a treeview.
    edit_mark = BoolProp()
    

    
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
    


