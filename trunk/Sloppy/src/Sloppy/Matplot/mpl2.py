"""
   An alternative implementation of a plotting Backend for SloppyPlot.

   @copyright: 2006, Niklas Volbers <mithrandir42@web.de>
"""


import gtk


from matplotlib.figure import Figure

if gtk.pygtk_version[1] > 8:
    from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvas
else:
    from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas

from Sloppy.Base import backend, objects, utils, globals
from Sloppy.Base.dataset import Dataset

import logging
logger = logging.getLogger('Backends.mpl2')
#------------------------------------------------------------------------------


# Problems with this implementation:
#  What if an object changes?

#  So obviously each painter needs to connect to its object somehow
#  and realize if it changes/if it is removed/if there's a new item.
#  This _should_ be done with the 'notify' and the 'notify::obj' 
#  signals, where the second version is for altering lists and dicts.
#  I should try this with the lines.

# Another thing:
#  Should the line be painted single or total ?

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


#------------------------------------------------------------------------------

class Backend(backend.Backend):

    def init(self):
        self.painters = {} # == layers

        self.active_layer = None
        #self.plot.sig_connect('notify::layers', self.on_notify_layers)


    def connect(self):
        self.figure = Figure(dpi=100, facecolor="white")
        self.canvas = FigureCanvas(self.figure)
        backend.Backend.connect(self)

    def disconnect(self):
        if self.canvas is not None:
            self.canvas.destroy()
            self.canvas = None
        if self.figure is not None:
            self.figure = None
        backend.Backend.disconnect(self)

    def get_painter(self, obj, klass):
        _id = id(obj)
        if self.painters.has_key(_id) is False:
            self.painters[_id] = klass(obj, parent=self)
        return self.painters[_id]

    def draw(self):
        for layer in self.plot.layers:
            painter = self.get_painter(layer, LayerPainter)
            painter.paint()

    def set_active_layer(self, layer):
        if layer == self.active_layer:
            return

        self.sig_emit("notify", {'active_layer':layer})
        self.active_layer = layer

    def on_notify_layers(self, sender, updateinfo):
        print "layers have changed:", updateinfo
        removed = updateinfo.get('removed', [])
        if self.active_layer in removed:
            self.set_active_layer(None)



#------------------------------------------------------------------------------

class Painter:

    def __init__(self, obj, parent):
        self.painters = {}
        self.parent = parent
        self.obj = obj

        if hasattr(self, 'init'):
            self.init()
        
    def get_painter(self, obj, klass):
        _id = id(obj)
        if self.painters.has_key(_id) is False:
            self.painters[_id] = klass(obj, parent=self)
        return self.painters[_id]

        
class LayerPainter(Painter):

    def init(self):
        self.axes = self.init_axes()

    def init_axes(self):
        return self.parent.figure.add_subplot('111')

    def paint(self):
        # plot_painter := backend
        layer, plot_painter = self.obj, self.parent
        axes = self.axes
            
        # title
        title = layer.title
        if title is not None:
            axes.set_title(title)

        # grid
        axes.grid(layer.grid)

        # legend
        legend = layer.legend        
        if legend is None:
            # remove any existing legend painter if obsolete
            pass
        else:
            p = self.get_painter(legend, LegendPainter)
            p.paint()
            
        
        for line in layer.lines:
            painter = self.get_painter(line, LinePainter)
            painter.paint()




class LinePainter(Painter):

    def paint(self):
        line, layer_painter = self.obj, self.parent
        layer = layer_painter.obj
        axes, backend = layer_painter.axes, layer_painter.parent

        #:line.visible
        if line.visible is False:
            if line in axes.lines:
                axes.lines.remove(line)
                               
        # data 
        ds = backend.get_line_source(line)
        cx, cy = backend.get_column_indices(line)
        try:
            xdata, ydata = backend.get_dataset_data(ds, cx, cy)
        except backend.BackendError, msg:            
            raise

        # row_first, row_last
        start, end = line.row_first, line.row_last        
        try:
            xdata = backend.limit_data(xdata, start, end)
            ydata = backend.limit_data(ydata, start, end)
        except BackendError, msg:
            riase

        index = layer.lines.index(line)

        # style, layer.group_style
        style = layer.group_style.get(line, index, line.style)

        global linestyle_mappings
        try: style = linestyle_mappings[style]
        except KeyError: style = linestyle_mappings.values()[1]

        #:line.marker
        #:layer.group_marker
        marker = layer.group_marker.get(line, index, line.marker)

        global linemarker_mappings
        try: marker = linemarker_mappings[marker]
        except KeyError: marker = linemarker_mappings.values()[0]
        
        #:line.width
        #:layer.group_width
        width = layer.group_width.get(line, index, line.width) or 1.0
        
        #:line.color
        #:layer.group_color
        color = layer.group_color.get(line, index, line.color) or 'black'

        #:line.marker_color
        marker_color = layer.group_marker_color.get(line, index, line.marker_color) or 'black'

        #:line.marker_siize
        marker_size = line.marker_size or 1

        # plot line!
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
            raise

        


class LegendPainter(Painter):

    def paint(self):
        legend, layer_painter = self.obj, self.parent

        kwargs = self.get_kwargs()
        border = kwargs.pop('border')
        visible = kwargs.pop('visible')
        handles, labels = kwargs.pop('handles'), kwargs.pop('labels')
        _legend = layer_painter.axes.legend(handles, labels, **kwargs)        
        _legend.draw_frame(border)
        _legend.set_visible(visible)
                

    def get_kwargs(self):
        legend, layer_painter = self.obj, self.parent

        # visible
        visible = legend.visible
                    
        # labels # TODO
        label = legend.label
        if label is not None:
            pass

        # border
        border = legend.border

        # position
        position = legend.position
        if position == 'at position':
            position = (legend.x, legend.y)

        # create legend entries from line labels
        lines = layer_painter.obj.lines
        labels = [l.label or "--" for l in lines]

        return  {'handles' : lines,
                 'labels' : labels,
                 'loc' : position,
                 'border' : border,
                 'visible' : visible}
        
#------------------------------------------------------------------------------    
globals.BackendRegistry['matplotlib2'] = Backend
