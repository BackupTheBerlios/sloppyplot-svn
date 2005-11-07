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


from Sloppy.Lib.Signals import HasSignals
from Sloppy.Lib.Undo import udict
from Sloppy.Lib.Props import *
       
        
map_system = {'data' : 0, 'graph': 1, 'screen': 2, 'display': 3}
map_valign = {'center':0, 'top':1, 'bottom':2}
map_halign = {'center':0, 'left':1, 'right': 2}

(GROUP_TYPE_CYCLE,
 GROUP_TYPE_FIXED,
 GROUP_TYPE_INCREMENT) = range(3)

map_groupproperty_types = {'cycle': GROUP_TYPE_CYCLE,
                           'fixed': GROUP_TYPE_FIXED,
                           'increment': GROUP_TYPE_INCREMENT}


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
    'line.marker' : ["None","points","pixels","circle symbols",
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
                   "steps"],
    'layer.type' : ['line2d', 'contour']
    }


#------------------------------------------------------------------------------
# BASE OBJECTS
#

class Group(HasProps):
    type = pInteger(ValueDict(map_groupproperty_types), default=0)
    allow_override = pBoolean(default=True)

def create_group(prop):
    class G(Group):
        value = Prop(prop.check, default=prop.on_default)
        cycle_list = pList(prop.check)
        increment = pFloat(default=1.0)
    return G

        

                    
class TextLabel(HasProps):
    " Single text label. "
    text = pUnicode(blurb="Displayed Text")
    x = pFloat(blurb="X-Position")
    y = pFloat(blurb="Y-Position")
    system = pInteger(ValueDict(map_system), default=0,
                      blurb="Coordinate System")
    valign = pInteger(ValueDict(map_valign), default=0,
                      blurb="Vertical Alignment")
    halign = pInteger(ValueDict(map_halign), default=0,
                      blurb="Horizontal Aligment")
    


class Axis(HasProps):
    " A single axis for a plot. "
    label = pUnicode(blurb='Label')
    start = pFloat(blurb='Start')
    end = pFloat(blurb='End')

    scale = pString(CheckValid(PV['axis.scale']), blurb='Scale',
                    default=PV['axis.scale'][0])
    format = pString(blurb='Format')


class Line(HasProps):
    " A single line or collection of points in a Plot. "
    label = pUnicode()
    cx = pInteger(CheckBounds(min=0), blurb="x-column", default=0)
    cy = pInteger(CheckBounds(min=0), blurb="y-column", default=1)
    row_first = pInteger(CheckBounds(min=0))
    row_last = pInteger(CheckBounds(min=0))
    #value_range = Prop(transform=str)    
    cxerr = pInteger(CheckBounds(min=0))
    cyerr = pInteger(CheckBounds(min=0))
    source = Prop(CheckType(Dataset))

    visible = pBoolean(default=True)
    
    style = Prop(CheckValid(PV['line.style']), default=PV['line.style'][0])    
    marker = Prop(CheckValid(PV['line.marker']), default=PV['line.marker'][0])
    width = pFloat(CheckBounds(min=0, max=10), default=1)   
    color = pString(default='g')


class Legend(HasProps):
    " Plot legend. "
    label = pUnicode(doc='Legend Label')
    visible = pBoolean(default=True)
    border = pBoolean(default=False)
    position = Prop(CheckValid(PV['legend.position']),
                    default=PV['legend.position'][0])
    x = pFloat(CheckBounds(min=0.0, max=1.0), default=0.7)
    y = pFloat(CheckBounds(min=0.0, max=1.0), default=0.0)


class Layer(HasProps, HasSignals):
    type = pString(CheckValid(PV['layer.type']),
                   default=PV['layer.type'][0])
    title = pUnicode(blurb="Title")
    lines = pList(CheckType(Line), blurb="Lines")
    grid = pBoolean(blurb="Grid", doc="Display a grid",
                    default=False)
    visible = pBoolean(blurb="Visible", default=True)
    legend = Prop(CheckType(Legend), reset=(lambda: Legend()))

    x = pFloat(CheckBounds(min=0.0, max=1.0), default=0.11)
    y = pFloat(CheckBounds(min=0.0, max=1.0), default=0.125)
    width = pFloat(CheckBounds(min=0.0, max=1.0), default=0.775)
    height = pFloat(CheckBounds(min=0.0, max=1.0), default=0.79)

    #
    # group properties
    #
    gLineStyle = create_group(Line.style)
    group_linestyle = Prop(CheckType(gLineStyle),
                           reset=gLineStyle(type=GROUP_TYPE_FIXED))

    gLineMarker = create_group(Line.marker)
    group_linemarker = Prop(CheckType(gLineMarker),
                            reset=gLineMarker(type=GROUP_TYPE_FIXED))

    gLineWidth = create_group(Line.width)
    group_linewidth = Prop(CheckType(gLineWidth),
                           reset=gLineWidth(type=GROUP_TYPE_FIXED))

    gLineColor = create_group(Line.color)
    group_linecolor = Prop(CheckType(gLineColor),
                           reset=gLineColor(type=GROUP_TYPE_CYCLE,
                                            cycle_list=['g','b','r']))
    #
    

    labels = pList(CheckType(TextLabel))

    # axes
    xaxis = Prop(CheckType(Axis), reset=(lambda:Axis()))
    yaxis = Prop(CheckType(Axis), reset=(lambda:Axis()))
    
    def get_axes(self):
        return {'x':self.xaxis, 'y':self.yaxis}
    axes = property(get_axes)

    def __init__(self, **kwargs):
        HasProps.__init__(self, **kwargs)

        HasSignals.__init__(self)
        self.sig_register('notify')
        self.sig_register('notify::labels')
        

class View(HasProps):
    start = pFloat(blurb='Start')
    end = pFloat(blurb='End')
    

class Plot(HasProps, HasSignals):
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

        HasSignals.__init__(self)
        self.sig_register("closed")
        self.sig_register("changed")
        
    #----------------------------------------------------------------------
    
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
    


