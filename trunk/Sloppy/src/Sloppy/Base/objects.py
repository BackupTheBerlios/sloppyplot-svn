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
from Sloppy.Lib.Props import HasProperties, Property, List, Dictionary
from Sloppy.Lib.Props.common import *
       
        
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

MAP = {

'line.marker':
{
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
}
}

#------------------------------------------------------------------------------
# BASE OBJECTS
#

class Group(HasProperties):
    type = Integer(mapping = map_groupproperty_types, default=0)
    allow_override = Boolean(default=True)

def create_group(prop):
    class G(Group):
        value = Property(prop.check, default=prop.on_default)
        cycle_list = List(prop.check)
        increment = Float(default=1.0)
    return G


class NewGroup(HasProperties):
    range_start = Float(default=1.0)
    range_end = Float(default=1.0)
    range_step = Float(default=1.0)

# range_xxx makes sense for line width, maybe for line color
# However, for marker and style we currently have strings.
# It might be possible to implement the long wanted ValueDict
# and make marker and style integer values. But then we would
# still have floats, not integers, 

                    
class TextLabel(HasProperties):
    " Single text label. "
    text = Unicode(blurb="Displayed Text")
    x = Float(blurb="X-Position")
    y = Float(blurb="Y-Position")
    system = Integer(mapping=map_system, default=0,
                      blurb="Coordinate System")
    valign = Integer(mapping=map_valign, default=0,
                      blurb="Vertical Alignment")
    halign = Integer(mapping=map_halign, default=0,
                      blurb="Horizontal Aligment")
    


class Axis(HasProperties):
    " A single axis for a plot. "
    label = Unicode(blurb='Label')
    start = Float(blurb='Start')
    end = Float(blurb='End')

    scale = String(valid=PV['axis.scale'], blurb="Scale", reset=PV['axis.scale'][0])
    format = String(blurb='Format')


class Line(HasProperties):
    " A single line or collection of points in a Plot. "
    label = Unicode()

    visible = Boolean(reset=True)
    style = Property(valid=PV['line.style'], default=PV['line.style'][0])    
    width = Float(range=(0,10), default=1)   
    color = String(default='g')

    #marker = Property(CheckValid(PV['line.marker']), default=PV['line.marker'][0])
    marker = Property(mapping=MAP['line.marker'], default=0)
    marker_color = String(default='black')

    # source stuff (soon deprecated)
    cx = Integer(range=(0,None), blurb="x-column", default=0)
    cy = Integer(range=(0,None), blurb="y-column", default=1)
    row_first = Property(coerce=int, range=(0,None))
    row_last = Property(coerce=int, range=(0,None))
    #value_range = Property(transform=str)    
    cxerr = Property(coerce=int, range=(0,None))
    cyerr = Property(coerce=int, range=(0,None))
    source = Property(type=Dataset)

    def source_to_string(self):

        source = '"%s"' % source.key

        if cx is None and cy is None:
            using = None
        else:
            using = 'using %s:%s' % (cx or '*', cy or '*')

        if row_first is None and row_last is None:
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
    visible = Boolean(reset=True)
    border = Boolean(reset=False)
    position = Property(valid=PV['legend.position'],
                    reset=PV['legend.position'][0])
    x = Float(range=(0.0,1.0), default=0.7)
    y = Float(range=(0.0,1.0), default=0.0)


class Layer(HasProperties, HasSignals):
    type = String(valid=PV['layer.type'], reset=PV['layer.type'][0])
    title = Unicode(blurb="Title")
    lines = List(type=Line, blurb="Lines")
    grid = Boolean(reset=False, blurb="Grid", doc="Display a grid")
    visible = Boolean(reset=True, blurb="Visible")
    legend = Property(type=Legend, reset=lambda: Legend())

    x = Float(range=(0.0,1.0), default=0.11)
    y = Float(range=(0.0,1.0), default=0.125)
    width = Float(range=(0.0,1.0), default=0.775)
    height = Float(range=(0.0,1.0), default=0.79)

    #
    # group properties
    #
    gLineStyle = create_group(Line.style)
    group_linestyle = Property(type=gLineStyle,
                               reset=gLineStyle(type=GROUP_TYPE_FIXED),
                               blurb="Line Style")

    gLineMarker = create_group(Line.marker)
    group_linemarker = Property(type=gLineMarker,
                                reset=gLineMarker(type=GROUP_TYPE_FIXED),
                                blurb="Line Marker")

    gLineWidth = create_group(Line.width)
    group_linewidth = Property(type=gLineWidth,
                           reset=gLineWidth(type=GROUP_TYPE_FIXED),
                           blurb="Line Width")

    gLineColor = create_group(Line.color)
    group_linecolor = Property(type=gLineColor,
                               reset=gLineColor(type=GROUP_TYPE_CYCLE,
                                                cycle_list=['g','b','r']),
                               blurb="Line Color")
    #
    

    labels = List(type=TextLabel)

    # axes
    xaxis = Property(type=Axis, reset=(lambda:Axis()))
    yaxis = Property(type=Axis, reset=(lambda:Axis()))
    
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
    
    legend = Property(type=Legend)
    lines = List(type=Line)
    labels = List(type=TextLabel)
    layers = List(type=Layer, blurb="Layers")

    views = List(type=View, blurb="Views")

    # might be used to notify the user that this
    # has been edited, e.g. by displaying a star
    # in a treeview.
    edit_mark = pBoolean()
    

    def __init__(self, *args, **kwargs):
        HasProperties.__init__(self, *args, **kwargs)

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
    


