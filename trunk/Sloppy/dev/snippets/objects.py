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

# $HeadURL: svn+ssh://niklasv@svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Base/objects.py $
# $Id: objects.py 403 2005-12-18 16:52:53Z niklasv $


"""
Collection of all basic data objects used for SloppyPlot.
"""
 
#from Sloppy.Base.dataset import Dataset

from Sloppy.Lib.Signals import HasSignals
from Sloppy.Lib.Undo import udict
from Sloppy.Lib.Props import HasProperties, Property
from Sloppy.Lib.Props.common import *
       
        
(GROUP_TYPE_CYCLE,
 GROUP_TYPE_FIXED,
 GROUP_TYPE_RANGE) = range(3)



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
    'layer.type' : ['line2d', 'contour'],

    'line.color' : ['green', 'red', 'blue', 'black'],
    'line.marker_color' : ['green', 'red', 'blue', 'black'],
    
    'group_linestyle_type' : [GROUP_TYPE_CYCLE, GROUP_TYPE_FIXED]
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

'group_type': {
    'cycle': GROUP_TYPE_CYCLE,
    'fixed': GROUP_TYPE_FIXED,
    'range': GROUP_TYPE_RANGE
    },

'group_linestyle_type': {
    'cycle': GROUP_TYPE_CYCLE,
    'fixed': GROUP_TYPE_FIXED,
    },

'group_linemarker_type': {
    'cycle': GROUP_TYPE_CYCLE,
    'fixed': GROUP_TYPE_FIXED,
    },

'group_linecolor_type': {
    'cycle': GROUP_TYPE_CYCLE,
    'fixed': GROUP_TYPE_FIXED,
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
    system = Property(MAP['position_system'],
                      blurb="Coordinate System")
    valign = Property(MAP['position_valign'],
                      blurb="Vertical Alignment")
    halign = Property(MAP['position_halign'],
                      blurb="Horizontal Aligment")
    


class Axis(HasProperties):
    " A single axis for a plot. "
    label = Unicode('', blurb='Label')
    start = Float(0.0, blurb='Start')
    end = Float(0.0, blurb='End')

    scale = Property(PV['axis.scale'])
    format = String('', blurb='Format')


a = Axis()
print a.scale
a.scale = 'log'
#a.scale = 'lalala'
print a.scale

# class Line(HasProperties):
#     " A single line or collection of points in a Plot. "
#     label = Unicode()

#     visible = Boolean(reset=True)
#     style = Property(valid=PV['line.style'], default=PV['line.style'][0])    
#     width = Float(range=(0,10), default=1)
#     # TODO: the color list PV['line.color'] should be a suggestion,
#     # TODO: not a requirement.
#     color = String(valid=PV['line.color'], default=PV['line.color'][0])

#     #marker = Property(CheckValid(PV['line.marker']), default=PV['line.marker'][0])
#     #marker = Property(mapping=MAP['line.marker'], default=0)
#     marker = Property(valid=PV['line.marker'],default=PV['line.marker'][0])
#     marker_color = String(valid=PV['line.marker_color'], default=PV['line.marker_color'][0])

#     # source stuff (soon deprecated)
#     cx = Integer(range=(0,None), blurb="x-column", default=0)
#     cy = Integer(range=(0,None), blurb="y-column", default=1)
#     row_first = Property(coerce=int, range=(0,None))
#     row_last = Property(coerce=int, range=(0,None))
#     #value_range = Property(transform=str)    
#     cxerr = Property(coerce=int, range=(0,None))
#     cyerr = Property(coerce=int, range=(0,None))
#     source = Property(type=Dataset)

#     def source_to_string(self):

#         source = '"%s"' % source.key

#         if cx is None and cy is None:
#             using = None
#         else:
#             using = 'using %s:%s' % (cx or '*', cy or '*')

#         if row_first is None and row_last is None:
#             rows = None
#         else:
#             rows = 'rows %s:%s' % (row_first or '*', row_last or '*')
            
#         return ' '.join((item for item in [source,using,rows] if item is not None))


#     def source_from_string(self, string):
#         # using regular expressions to parse the string
#         # TODO: this does not work yet
#         regexp = '(?P<source>\".*\"|[^ ]+)(\s+using\s+(?P<using>.+))?(\s+rows\s+(?P<rows>.+))?'
        
        



class Legend(HasProperties):
    " Plot legend. "
    label = Unicode(doc='Legend Label')
    visible = Boolean(True)
    border = Boolean(False)
    position = Property(PV['legend.position'])   
    x = FloatRange(0.0, 1.0, default=0.7)
    y = FloatRange(0.0, 1.0, default=0.0)


# class Layer(HasProperties, HasSignals):
#     type = String(valid=PV['layer.type'], reset=PV['layer.type'][0])
#     title = Unicode(blurb="Title")
#     lines = List(type=Line, blurb="Lines")
#     grid = Boolean(reset=False, blurb="Grid", doc="Display a grid")
#     visible = Boolean(reset=True, blurb="Visible")
#     legend = Property(type=Legend, reset=lambda o,k: Legend())

#     x = Float(range=(0.0,1.0), default=0.11)
#     y = Float(range=(0.0,1.0), default=0.125)
#     width = Float(range=(0.0,1.0), default=0.775)
#     height = Float(range=(0.0,1.0), default=0.79)

#     #
#     # Group Properties
#     #
#     class GroupLineStyle(HasProperties):
#         type = Integer(mapping=MAP['group_linestyle_type'], reset=GROUP_TYPE_FIXED)
#         allow_override = Boolean(reset=True)        
#         value = Property(Line.style.check, reset=Line.style.on_default)
#         cycle_list = List(Line.style.check)
#         range_start = Float(reset=1.0)
#         range_stop = Float(reset=None)
#         range_step = Float(reset=1.0)
        
#     group_linestyle = Property(type=GroupLineStyle,                               
#                                reset=lambda o,k:Layer.GroupLineStyle(),
#                                blurb="Line Style")


#     class GroupLineMarker(HasProperties):
#         type = Integer(mapping=MAP['group_linemarker_type'], reset=GROUP_TYPE_FIXED)
#         allow_override = Boolean(reset=True)        
#         value = Property(Line.marker.check, reset=Line.marker.on_default)
#         cycle_list = List(Line.marker.check)
#         range_start = Float(reset=1.0)
#         range_stop = Float(reset=None)
#         range_step = Float(reset=1.0)
        
#     group_linemarker = Property(type=GroupLineMarker,
#                                 reset=lambda o,k:Layer.GroupLineMarker(),
#                                 blurb="Line Marker")

    
#     class GroupLineWidth(HasProperties):
#         type = Integer(mapping=MAP['group_type'], reset=GROUP_TYPE_FIXED)
#         allow_override = Boolean(reset=True)        
#         value = Property(Line.width.check, reset=Line.width.on_default)
#         cycle_list = List(Line.width.check)
#         range_start = Float(reset=1.0)
#         range_stop = Float(reset=None)
#         range_step = Float(reset=1.0)
        
#     group_linewidth = Property(type=GroupLineWidth,
#                            reset=lambda o,k:Layer.GroupLineWidth(),
#                            blurb="Line Width")

#     class GroupLineColor(HasProperties):
#         type = Integer(mapping=MAP['group_linecolor_type'], reset=GROUP_TYPE_CYCLE)
#         allow_override = Boolean(reset=True)        
#         value = Property(Line.color.check, reset=Line.color.on_default)
#         cycle_list = List(Line.color.check, reset=lambda o,k:['g','b','r'])
#         range_start = Float(reset=1.0)
#         range_stop = Float(reset=None)
#         range_step = Float(reset=1.0)
        
#     group_linecolor = Property(type=GroupLineColor,
#                                reset=lambda o,k:Layer.GroupLineColor(),
#                                blurb="Line Color")


#     #   
#     labels = List(type=TextLabel)

#     # axes
#     xaxis = Property(type=Axis, reset=lambda o,k:Axis())
#     yaxis = Property(type=Axis, reset=lambda o,k:Axis())
    
#     def get_axes(self):
#         return {'x':self.xaxis, 'y':self.yaxis}
#     axes = property(get_axes)

#     def __init__(self, **kwargs):
#         HasProperties.__init__(self, **kwargs)

#         HasSignals.__init__(self)
#         self.sig_register('notify')
#         self.sig_register('notify::labels')
        

# class View(HasProperties):
#     start = Float(blurb='Start')
#     end = Float(blurb='End')
    

# class Plot(HasProperties, HasSignals):
#     key = Keyword(blurb="Key")

#     title = Unicode(blurb="Title")
#     comment = Unicode(blurb="Comment")
    
#     legend = Property(type=Legend)
#     lines = List(type=Line)
#     labels = List(type=TextLabel)
#     layers = List(type=Layer, blurb="Layers")

#     views = List(type=View, blurb="Views")

#     # might be used to notify the user that this
#     # has been edited, e.g. by displaying a star
#     # in a treeview.
#     edit_mark = pBoolean()
    

#     def __init__(self, *args, **kwargs):
#         HasProperties.__init__(self, *args, **kwargs)

#         HasSignals.__init__(self)
#         self.sig_register("closed")
#         self.sig_register("changed")
        
#     #----------------------------------------------------------------------
    
#     def close(self):
#         self.sig_emit('closed')        

#     def detach(self):
#         self.sig_emit('closed')        
    


# #------------------------------------------------------------------------------
# # Factory Methods
# #

# def new_lineplot2d(**kwargs):
#     """
#     Create a one-layer line plot with the given keyword arguments.
#     Arguments that do not match a Plot property are passed on to
#     the Layer.
#     """

#     plot = Plot()
    
#     # pass only those keywords to the plot that are meaningful
#     plot_kwargs = dict()
#     for key in plot.get_props().keys():
#         if kwargs.has_key(key):
#             plot_kwargs[key] = kwargs.pop(key)
#     plot.set_values(**plot_kwargs)

#     # ...and then create the appropriate layer, assuming
#     # that all remaining keyword arguments are meant for the layer
#     kwargs.update( {'type' : 'line2d'} )
#     plot.layers = [Layer(**kwargs)]
    
#     return plot
    


