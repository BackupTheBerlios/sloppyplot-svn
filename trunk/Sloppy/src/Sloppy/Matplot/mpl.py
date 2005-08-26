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
An implementation of the Plotter object using matplotlib.
"""

import pygtk  # TBR
pygtk.require('2.0') # TBR

import gtk

import logging
logger = logging.getLogger('Backends.mpl')

from matplotlib import *

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas

from Sloppy.Base import backend
from Sloppy.Base.backend import BackendRegistry
from Sloppy.Base import objects
from Sloppy.Base import utils, uwrap
from Sloppy.Base.dataset import Dataset
from Sloppy.Base.table import Table



linestyle_mappings = \
{'None'               : "None",
 "solid"              : "-",
 "dashed"             : "--",
 "dash-dot"           : "-.",
 "dotted"             : ":",
 "steps"              : "steps"
}


# marker=
linemarker_mappings = \
{'None'                    : 'None',
 "points"                  : ".",
 "pixels"                  : ",",
 "circle symbols"          : "o",
 "triangle up symbols"     : "^",
 "triangle down symbols"   : "v",
 "triangle left symbols"   : "<",
 "triangle right symbols"  : ">",
 "square symbols"          : "s",             
 "plus symbols"            : "+",
 "cross symbols"           : "x",
 "diamond symbols"         : "D",
 "thin diamond symbols"    : "d",
 "tripod down symbols"     : "1",
 "tripod up symbols"       : "2",
 "tripod left symbols"     : "3",
 "tripod right symbols"    : "4",
 "hexagon symbols"         : "h",
 "rotated hexagon symbols" : "H",
 "pentagon symbols"        : "p",
 "vertical line symbols"   : "|",
 "horizontal line symbols" : "_"
 }



class Backend( backend.Plotter ):

    def init(self):
        # line_cache: key = id(Curve), value=mpl line object
        self.line_cache = dict()
        
        self.layer_to_axes = dict()
        self.axes_to_layer = dict()
        self.layers_cache = list() # copy of self.plot.layers
        
    def connect(self):
        logger.debug("Opening matplotlib session.")        

        self.figure = Figure(dpi=100, facecolor="white")  # figsize=(5,4), dpi=100)        
        self.canvas = FigureCanvas(self.figure)
        self.canvas.show()

        self.line_cache.clear()
        self.layer_to_axes.clear()
        self.axes_to_layer.clear()

        backend.Plotter.connect(self)
        logger.debug("Init finished")


    def disconnect(self):
        logger.debug("Closing matplotlib session.")

        if not self.canvas is None:
            self.canvas.destroy()
            self.canvas = None
        if not self.figure is None:
            self.figure = None
        
        backend.Plotter.disconnect(self)


    #----------------------------------------------------------------------

    def arrange(self, rows=1, cols=1):

        layers = self.plot.layers
        n = len(layers)

        if n > (rows*cols):
            rows = int((rows*cols) / n) + 1
            cols = rows * n
            #raise ValueError("Not enough rows and cols for all layers!")

        self.figure.clear()
        self.figure.axes = []
        
        self.layer_to_axes.clear()
        self.axes_to_layer.clear()
        self.layers_cache = list()
        j = 1
        for layer in layers:
            print "Setting up layer", layer
            axes = self.figure.add_subplot("%d%d%d" % (rows,cols,j))
            self.layer_to_axes[layer] = axes
            self.axes_to_layer[axes] = layer
            self.layers_cache.append(layer)
            j += 1
        

        
    def draw_layer(self, layer, group_info):

        ax = self.layer_to_axes[layer]

        print "DRAWING AXES ", ax
        ax.lines = []

        line_cache = []
        line_count = 0
        last_cx = -1

        # Default values come in two flavors:
        # group-wise and single default values        
        group_colors = uwrap.get(layer, 'group_colors')
        group_styles = uwrap.get(layer, 'group_styles')
        group_markers = uwrap.get(layer, 'group_markers')

        #default_color = 'r'
        default_color = None
        default_style = 'solid'
        default_marker = 'None'
        

        #:layer.visible
        if uwrap.get(layer, 'visible') is False:
            return

        #:layer.title
        title = uwrap.get(layer, 'title', None)
        if title is not None:
            ax.set_title(title)        

        #:layer.grid
        grid = uwrap.get(layer, 'grid')
        ax.grid(grid)                         

        #:layer.lines
        for line in layer.lines:
            data_to_plot = []
            
            #:line.visible
            if uwrap.get(line, 'visible') is False:
                if line in ax.lines:
                    ax.lines.remove(line)
                continue

            #:line.source            
            if line.source is None:
                logger.warn("No Dataset specified for Line!")
                continue
            else:
                ds = line.source
                
            if ds.is_empty() is True:
                logger.warn("No data for Line!")
                continue

            table = ds.get_data()
            if not isinstance(table, Table):
                raise TypeError("Matplotlib Backend currently only supports data of type Table, while this is of %s"
                                % type(table))

            #:line.cx
            if line.cx is None or line.cy is None:
                logger.error("No x or y source given for Line. Line skipped.")
                continue
            else:
                cx, cy = line.cx, line.cy
            
            try:
                xdata = table[cx]
            except IndexError:
                logger.error("X-Index out of range (%s). Line skipped." % cx)
                continue


            #:line.cy
            try:
                ydata = table[cy]
            except IndexError:
                logger.error("Y-Index out of range (%s). Line skipped." % cy)
                continue


            #:line.row_first
            #:line.row_last
            start, end = line.row_first, line.row_last
            try:
                xdata = xdata[start:end]
                ydata = ydata[start:end]
            except IndexError:
                logger.error("Index range '%s'out of bounds!" % (start,end) )
                continue
            

            #:line.style
            global linestyle_mappings
            default = default_style or group_styles[line_count % len(group_styles)]
            style = uwrap.get(line, 'style', default)
            style = linestyle_mappings[style]


            #:line.marker
            global linemarker_mappings
            default = default_marker or group_markers[line_count % len(group_markers)]
            marker = uwrap.get(line, 'marker', default)
            marker = linemarker_mappings[marker]


            #:line.width
            width = uwrap.get(line, 'width')

            
            #:line.color
            default = default_color or group_colors[line_count % len(group_colors)]
            color = uwrap.get(line, 'color', default)


            #--- PLOT LINE ---
            l, = ax.plot( xdata, ydata,
                          linewidth=width,
                          linestyle=style,
                          marker=marker,
                          color=color)
            line_cache.append(l)
            
            # TODO: if we set the label afterwards, don't we then have a redraw?
            #:line.label
            label = line.label
            if label is None:
                column = table.column(cy)
                label = column.label or column.key or uwrap.get(line, 'label')
            l.set_label(label)

            line_count += 1

#         #
#         # additional lines
#         #
#         p = len(xdata)
#         if p > 2: p = p/2
#         atpoint = xdata[max(p-1,0)]
#         print "Printing vertical line at ", atpoint
#         ax.axvline(atpoint)
        
        #:layer.legend
        legend = uwrap.get(layer, 'legend')
        if legend is not None and line_count > 0:
            visible = uwrap.get(legend, 'visible')
            if visible is True:
                #:legend.label:TODO
                label = uwrap.get(legend, 'visible')
                if label is not None:
                    pass

                #:legend.border:OK
                # (see below but keep it here!)
                border = uwrap.get(legend, 'border')
                                                
                #:legend.position TODO
                position = uwrap.get(legend, 'position', 'best')
                if position == 'at position':
                    position = (uwrap.get(legend, 'x'), uwrap.get(legend, 'y'))

                # create legend entries from line labels
                labels = [l.get_label() for l in line_cache]                
                
                legend = ax.legend(line_cache, labels, loc=position, pad=0.8)
                legend.draw_frame(border)

            else:
                ax.legend_ = None
        else:
            ax.legend_ = None

        #:layer.axes
        for (key, axis) in layer.axes.iteritems():
            #:axis.label
            #:axis.scale
            #:axis.start
            #:axis.end
            label = uwrap.get(axis, 'label')            
            scale = uwrap.get(axis, 'scale')
            start = uwrap.get(axis, 'start')
            end = uwrap.get(axis, 'end')
            print "START = %s, END = %s" % (str(start), str(end))
            if key == 'x':
                set_label = ax.set_xlabel
                set_scale = ax.set_xscale
                set_start = (lambda l: ax.set_xlim(xmin=l))
                set_end = (lambda l: ax.set_xlim(xmax=l))
            elif key == 'y':
                set_label = ax.set_ylabel
                set_scale = ax.set_yscale
                set_start = (lambda l: ax.set_ylim(ymin=l))
                set_end = (lambda l: ax.set_ylim(ymax=l))
            else:
                raise RuntimeError("Invalid axis key '%s'" % key)

            if label is not None: set_label(label)
            if scale is not None: set_scale(scale)
            if start is not None: set_start(start)
            if end is not None: set_end(end)  




    def draw(self):
        logger.debug("Matplotlib: draw()")
        
        self.check_connection()
               
        # plot all curves together in one plot
        legend_list = [] # for legend later on
        curve_count = 0
       
        #
        if self.plot.layers != self.layers_cache:
            self.arrange()

        for layer in self.plot.layers:
            group_info = {}
            self.draw_layer(layer, group_info)
       
        self.canvas.draw()


#------------------------------------------------------------------------------


class BackendWithWindow(Backend):

    def connect(self):
        win = gtk.Window()        
        Backend.connect(self)
        win.add(self.canvas)
        win.connect("destroy", Backend.disconnect(self))
        win.show()

        
    def disconnect(self):
        win.destroy()
        

#------------------------------------------------------------------------------
BackendRegistry.register('matplotlib', Backend)
BackendRegistry.register('matplotlib/w', Backend)


            
