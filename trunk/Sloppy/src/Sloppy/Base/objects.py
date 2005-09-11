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
    width = pFloat(CheckBounds(min=0, max=10))
    style = Prop(CheckValid(PV['line.style']))
    marker = Prop(CheckValid(PV['line.marker']))
    color = pString()
    visible = pBoolean()


class Legend(HasProps):
    " Plot legend. "
    label = pUnicode(doc='Legend Label')
    visible = pBoolean()
    border = pBoolean()
    position = pString(value_list=PV['legend.position'])
    x = pFloat(CheckBounds(min=0.0, max=1.0))
    y = pFloat(CheckBounds(min=0.0, max=1.0))


class Layer(HasProps):
    type = pString(CheckValid(PV['layer.type']))
    title = pUnicode(blurb="Title")
    axes = pDictionary(CheckType(Axis), blurb="Axes")
    lines = pList(CheckType(Line), blurb="Lines")
    grid = pBoolean(blurb="Grid", doc="Display a grid")
    visible = pBoolean(blurb="Visible")
    legend = Prop(CheckType(Legend), reset=(lambda: Legend()))

    x = pFloat(CheckBounds(min=0.0, max=1.0))
    y = pFloat(CheckBounds(min=0.0, max=1.0))
    width = pFloat(CheckBounds(min=0.0, max=1.0))
    height = pFloat(CheckBounds(min=0.0, max=1.0))

    group_colors = pString()
    group_styles = pList(CheckType(str))
    group_markers = pList(CheckType(str))

    def request_axis(self, key, undolist=[]):
        if self.axes.has_key(key) is False:            
            udict.setitem( self.axes, key, Axis(), undolist=undolist)
        return self.axes[key]        
    
    
class TextLabel(HasProps):
    " Single text label. "
    text = pUnicode()
    
    x = pFloat()
    y = pFloat()



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
    


