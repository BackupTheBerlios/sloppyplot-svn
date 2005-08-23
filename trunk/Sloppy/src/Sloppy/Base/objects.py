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
from Sloppy.Lib.Props import Container, Prop, ListProp, DictProp, BoolProp, RangeProp

        
        

#------------------------------------------------------------------------------
# BASE OBJECTS

class Axis(Container):
    " A single axis for a plot. "
    label = Prop(cast=unicode, blurb='Label')
    start = Prop(cast=float, blurb='Start')
    end = Prop(cast=float, blurb='End')

    scale = Prop(types=str, blurb='Scale', values=PV['axis.scale'])
    format = Prop(types=str, blurb='Format')


class Line(Container):
    " A single line or collection of points in a Plot. "
    label = Prop(cast=unicode)
    cx = RangeProp(cast=int, min=0, blurb="x-column")
    cy = RangeProp(cast=int, min=0, blurb="y-column")
    index_first = RangeProp(cast=int,min=0)
    index_last = RangeProp(cast=int,min=0)
    #value_range = Prop(cast=str)    
    cxerr = RangeProp(cast=int, min=0)
    cyerr = RangeProp(cast=int, min=0)
    source = Prop(types=Dataset)
    width = RangeProp(cast=float, min=0, max=10)
    style = Prop(values=PV['line.style'])
    marker = Prop(values=PV['line.marker'])
    color = Prop(cast=str)
    visible = BoolProp()


class Legend(Container):
    " Plot legend. "
    label = Prop(cast=unicode, doc='Legend Label')
    visible = BoolProp()
    border = BoolProp()
    position = Prop(types=str, values=PV['legend.position'])
    x = RangeProp(cast=float, min=0.0, max=1.0)
    y = RangeProp(cast=float, min=0.0, max=1.0)


class Layer(Container):
    type = Prop(types=str, values=PV['layer.type'])
    title = Prop(cast=unicode, blurb="Title")
    axes = DictProp(types=Axis, blurb="Axes")
    lines = ListProp(types=Line, blurb="Lines")
    grid = BoolProp(blurb="Grid", doc="Display a grid")
    visible = BoolProp(blurb="Visible")
    legend = Prop(types=Legend)

    x = RangeProp(types=float, min=0.0, max=1.0)
    y = RangeProp(types=float, min=0.0, max=1.0)
    width = RangeProp(types=float, min=0.0, max=1.0)
    height = RangeProp(types=float, min=0.0, max=1.0)    

    group_colors = Prop(types=str)
    group_styles = ListProp(types=str)
    group_markers = ListProp(types=str)
    
    def __init__(self,**kwargs):
        Container.__init__(self, **kwargs)
        if self.legend is None:
            self.legend = Legend()

    def request_axis(self, key, undolist=[]):
        if self.axes.has_key(key) is False:            
            udict.setitem( self.axes, key, Axis(), undolist=undolist)
        return self.axes[key]        
    
    
class TextLabel(Container):
    " Single text label. "
    text = Prop(cast=unicode)
    
    x = Prop(cast=float)
    y = Prop(cast=float)



class View(Container):
    start = Prop(cast=float, blurb='Start')
    end = Prop(cast=float, blurb='End')
    

class Plot(Container):
    key = Prop(types=str, blurb="Key")

    title = Prop(cast=unicode, blurb="Title")
    comment = Prop(cast=unicode, blurb="Comment")
    
    legend = Prop(types=Legend)
    lines = ListProp(types=Line)
    labels = ListProp(types=TextLabel)
    layers = ListProp(types=Layer, blurb="Layers")

    views = ListProp(types=View, blurb="Views")

    # might be used to notify the user that this
    # has been edited, e.g. by displaying a star
    # in a treeview.
    edit_mark = BoolProp()
    
    def __init__(self,**kwargs):
        Container.__init__(self, **kwargs)
    
    def close(self):
        Signals.emit(self, 'closed')

    def detach(self):
        Signals.emit(self, 'closed')
    


#------------------------------------------------------------------------------
# factory methods

def new_lineplot2d(**kwargs):
    """
    Create a one-layer line plot with the given keyword arguments.
    Arguments that do not match a Plot property are passed on to
    the Layer.
    """
    
    # pass only those keywords to the plot that are meaningful
    plot_kwargs = dict()
    for key in Plot.get_propdict().keys():
        if kwargs.has_key(key):
            plot_kwargs[key] = kwargs.pop(key)

    # create new plot...
    plot = Plot(**plot_kwargs)

    # ...and then create the appropriate layer, assuming
    # that all remaining keyword arguments are meant for the layer
    kwargs.update( {'type' : 'line2d'} )
    plot.layers = [Layer(**kwargs)]
    
    return plot
    


