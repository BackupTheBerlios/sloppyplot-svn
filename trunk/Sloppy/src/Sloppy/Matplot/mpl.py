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
An implementation of the Backend object using matplotlib.
"""


import gtk, inspect, matplotlib
from matplotlib import * # maybe remove this?

import logging
logger = logging.getLogger('Backends.mpl')

from matplotlib.figure import Figure

if gtk.pygtk_version[1] > 8:
    from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvas
else:
    from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas

from matplotlib.text import Text

from Sloppy.Base import backend, objects, utils, globals
from Sloppy.Base.dataset import Dataset
#------------------------------------------------------------------------------

# Horizontal/vertical lines in mpl:
#  self.lx, = ax.plot( (0,0), (0,0), 'k-' ) # horiz line
#  self.ly, = ax.plot( (0,0), (0,0), 'k-' ) # vert line
#
#  # text location in axes coords
#  self.txt = ax.text( 0.7, 0.9, '', transform=ax.transAxes)
#
#  # update line positions
#  self.lx.set_data( (minx, maxx), (y,y) )
#  self.ly.set_data( (x,x), (miiny, maxy) )
#
#  self.txt.set_text( 'x=%1.2f, y=%1.2f' % (x,y) )
#  draw()

# -------- See also: axvline for such a function

#------------------------------------------------------------------------------


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



class Backend( backend.Backend ):

    def init(self):
        
        self.layer_to_axes = {}
        self.axes_to_layer = {}
        self.layers_cache = [] # copy of self.plot.layers
        self.layer_cblists = {}

        self.line_caches = {}
        self.omaps = {}
        
        
    def connect(self):
        logger.debug("Opening matplotlib session.")        

        self.figure = Figure(dpi=100), facecolor="white")  # figsize=(5,4), dpi=100)        
        self.canvas = FigureCanvas(self.figure)
        self.canvas.show()

        self.line_caches = {}
        self.layer_to_axes.clear()
        self.axes_to_layer.clear()

        backend.Backend.connect(self)
        logger.debug("Init finished")


    def set(self, project,plot):
        backend.Backend.set(self, project, plot)
        if self.project is not None:
            # TODO: connect to update::layers of Plot
            pass

    def disconnect(self):
        logger.debug("Closing matplotlib session.")

        if not self.canvas is None:
            self.canvas.destroy()
            self.canvas = None
        if not self.figure is None:
            self.figure = None
        
        backend.Backend.disconnect(self)

        

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
        self.layers_cache = []

        for cblist in self.layer_cblists.itervalues():
            for cb in cblist:
                cb.disconnect()
        self.layer_cblists = {}
        
        j = 1
        for layer in layers:
            print "Setting up layer", layer
            axes = self.figure.add_subplot("%d%d%d" % (rows,cols,j))
            self.layer_to_axes[layer] = axes
            self.axes_to_layer[axes] = layer
            self.layers_cache.append(layer)

            print "Connecting to update of ", layer
            self.layer_cblists[layer] = \
              [layer.sig_connect('update', self.on_update_layer),
               layer.sig_connect('update::labels', self.on_update_labels)
               ]

            j += 1


    def draw(self):
        self.check_connection()
        logger.debug("Matplotlib: draw()")                
             
        if self.plot.layers != self.layers_cache:
            self.arrange()

        self.omaps = {}
        for layer in self.plot.layers:            
            self.update_layer(layer)
        self.draw_canvas()
        
    def draw_canvas(self):
        self.canvas.draw()        


    #----------------------------------------------------------------------
    # Layer
    #
    
    def on_update_layer(self, sender, updateinfo={}):
        # updateinfo is ignored
        self.update_layer(sender)
        self.canvas.draw()
    
    def update_layer(self, layer, updateinfo={}):
        # updateinfo is ignored

        self.omaps[layer] = {}
        self.line_caches[layer] = {}

        axes = self.layer_to_axes[layer]        
        axes.lines = []
        line_cache = self.line_caches[layer] = []        

        #:layer.lines:OK
        for line in layer.lines:
            self.update_line(line, layer, axes=axes)

        #:layer.axes
        for (key, axis) in layer.axes.iteritems():
            #:axis.label
            #:axis.scale
            #:axis.start
            #:axis.end
            label = axis.label
            scale = axis.scale
            start = axis.start
            end = axis.end

            #logger.debug("start = %s; end = %s" % (start, end))
            
            if key == 'x':
                set_label = axes.set_xlabel
                set_scale = axes.set_xscale
                set_start = (lambda l: axes.set_xlim(xmin=l))
                set_end = (lambda l: axes.set_xlim(xmax=l))
            elif key == 'y':
                set_label = axes.set_ylabel
                set_scale = axes.set_yscale
                set_start = (lambda l: axes.set_ylim(ymin=l))
                set_end = (lambda l: axes.set_ylim(ymax=l))
            else:
                raise RuntimeError("Invalid axis key '%s'" % key)

            if label is not None: set_label(label)
            if scale is not None: set_scale(scale)
            if start is not None: set_start(start)
            if end is not None: set_end(end)
            
        #:layer.visible
        if layer.visible is False:
            return

        # TODO
        #:layer.title
        title = layer.title
        if title is not None:
            axes.set_title(title)

        #:layer.grid
        axes.grid(layer.grid)
                    
        #:layer.legend:OK
        self.update_legend(layer)

        #:layer.labels:OK
        axes.texts = []
        for label in layer.labels:
            self.update_textlabel(label, layer)

        
    #----------------------------------------------------------------------
    # Line
    #
    
    def update_line(self, line, layer, axes=None, updateinfo={}):
        # updateinfo is ignored
        
        axes = axes or self.layer_to_axes[layer]
        omap = self.omaps[layer]
        line_cache = self.line_caches[layer]

        data_to_plot = []

        #:line.visible
        if line.visible is False:
            if line in axes.lines:
                axes.lines.remove(line)
                line_cache.remove(line)
            omap[line] = None                    
            return

        ds = self.get_line_source(line)
        cx, cy = self.get_column_indices(line)
        try:
            xdata, ydata = self.get_dataset_data(ds, cx, cy)
        except backend.BackendError, msg:            
            logger.error(msg)
            omap[line] = None
            return
            

        #:line.row_first
        #:line.row_last
        start, end = line.row_first, line.row_last        
        try:
            xdata = self.limit_data(xdata, start, end)
            ydata = self.limit_data(ydata, start, end)
        except BackendError, msg:
            logger.error("Error when plotting line #%d: %s" % (line_index, msg))
            omap[line] = None
            return

        line_index = layer.lines.index(line)

        #:line.style
        #:layer.group_style
        style = layer.group_style.get(line, line_index, line.style)

        global linestyle_mappings
        try: style = linestyle_mappings[style]
        except KeyError: style = linestyle_mappings.values()[1]

        #:line.marker
        #:layer.group_marker
        marker = layer.group_marker.get(line, line_index, line.marker)

        global linemarker_mappings
        try: marker = linemarker_mappings[marker]
        except KeyError: marker = linemarker_mappings.values()[0]
        
        #:line.width
        #:layer.group_width
        width = layer.group_width.get(line, line_index, line.width) or 1.0
        
        #:line.color
        #:layer.group_color
        color = layer.group_color.get(line, line_index, line.color) or 'black'

        #:line.marker_color
        marker_color = layer.group_marker_color.get(line, line_index, line.marker_color) or 'black'

        #:line.marker_siize
        marker_size = line.marker_size or 1
        
        #--- PLOT LINE ---
        try:
            l, = axes.plot( xdata, ydata,
                            linewidth=width,
                            linestyle=style,
                            marker=marker,
                            color=color,
                            markerfacecolor=marker_color,
                            markeredgecolor=marker_color,
                            markersize=marker_size)
        except Exception, msg:
            logger.error("Error when plotting line %d: %s" % (line_index, msg))
            omap[line] = None
            return

        line_cache.append(l)
        omap[line] = l        

        label = self.get_line_label(line, dataset=ds, cy=cy)
        if label is not None:
            l.set_label(label)

    
    #----------------------------------------------------------------------
    # TextLabel
    #

    def on_update_labels(self, layer, updateinfo={}):
        # updateinfo is ignored

        # clear existing labels and their corresponding mappings
        axes = self.layer_to_axes[layer]        
        axes.texts = []
        for label in layer.labels:
            try:
                self.omaps[layer].pop(label)
            except KeyError:
                pass
            
        # create new labels
        for label in layer.labels:            
            self.update_textlabel(label, layer)

        self.canvas.draw()        
    
    def update_textlabel(self, label, layer, axes=None, updateinfo={}):
        # updateinfo is ignored
        
        axes = axes or self.layer_to_axes[layer]
        kwargs = self.label_kwargs(axes, label)
        if kwargs is None:
            return
        transform = kwargs.pop('transform')

        try:
            mpl_label = self.omaps[layer][label]
        except KeyError:
            mpl_label = Text(**kwargs)
            self.omaps[layer][label] = mpl_label
            axes.texts.append(mpl_label)
        else:
            mpl_label.update(kwargs)

        mpl_label.set_transform(transform)

        
    def label_kwargs(self, axes, label):
        if label.x is None or label.y is None:
            logger.info("Label coordinates contains empty value. Skipped.")
            return None

        if label.system == 'data':
            transform = axes.transData
        elif label.system == 'graph':
            transform = axes.transAxes
        elif label.system == 'screen':
            transform = self.figure.transFigure
        elif label.system == 'display':
            transform = matplotlib.transforms.identity_transform()

        return {'x': label.x, 'y': label.y, 'text' : label.text,
                'horizontalalignment': 'center',
                'verticalalignment' : 'center',
                'transform' : transform}


    #----------------------------------------------------------------------
    # Legend
    #
    
    def update_legend(self, layer, axes=None, updateinfo={}):
        # updateinfo is ignored
        axes = axes or self.layer_to_axes[layer]
        legend = layer.legend
        if legend is None:
            if axes.legend_ is not None:
                axes.legend_ = None
            self.omaps[layer][legend] = None
        else:
            kw = self.legend_kwargs(legend, layer)
            border = kw.pop('border')
            visible = kw.pop('visible')
            handles, labels = kw.pop('handles'), kw.pop('labels')
            _legend = axes.legend(handles, labels, **kw)
            self.omaps[layer][legend] = _legend
            _legend.draw_frame(border)
            _legend.set_visible(visible)

        self.omaps[layer][legend] = axes.legend_

    
    def legend_kwargs(self, legend, layer):
        """
        'border' must be popped and set via legend.draw_frame
        'visible' must be popped and set via set_visible
        """

        visible = legend.visible
                    
        #:legend.label:TODO
        label = legend.label
        if label is not None:
            pass

        #:legend.border:OK
        # (see below but keep it here!)
        border = legend.border

        #:legend.position TODO
        position = legend.position
        if position == 'at position':
            position = (legend.x, legend.y)

        # create legend entries from line labels
        line_cache = self.line_caches[layer]
        labels = [l.get_label() for l in line_cache]

        return  {'handles' : line_cache,
                 'labels' : labels,
                 'loc' : position,
                 'border' : border,
                 'visible' : visible}



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
#globals.BackendRegistry['matplotlib'] = Backend
#globals.BackendRegistry['matplotlib/w'] = BackendWithWindow

