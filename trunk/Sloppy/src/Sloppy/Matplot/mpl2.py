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
from Sloppy.Base.objects import SPObject, Line
from Sloppy.Base.dataset import Dataset
from Sloppy.Lib.Check import Instance, Undefined, Dict, AnyValue

import logging
logger = logging.getLogger('Backends.mpl2')
#------------------------------------------------------------------------------


# Problems with this implementation:
#  What if an object changes?

#  So obviously each painter needs to connect to its object somehow
#  and realize if it changes/if it is removed/if there's a new item.
#  This _should_ be done with the 'update' and the 'update:obj' 
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

class Painter(SPObject):

    def __init__(self, obj, parent):
        SPObject.__init__(self)
        
        self.painters = {}
        self.parent = parent
        self.obj = obj

        if hasattr(self, 'init'):
            self.init()

    def paint(self):
        # update all
        self.update(self.obj, self.obj._checks.keys())
        
    def get_painter(self, obj, klass):
        _id = id(obj)
        try:
            return self.painters[_id]
        except KeyError, msg:
            if klass is not None:
                new_painter = klass(obj, parent=self)
                self.painters[_id] = new_painter
                return new_painter
            else:
                raise

    def get_backend(self):
        obj = self
        while not isinstance(obj, Backend):
            obj = obj.parent
        return obj
                
        


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
        line_cache = layer_painter.axes.lines
        labels = [l.get_label() for l in line_cache]

        return  {'handles' : line_cache,
                 'labels' : labels,
                 'loc' : position,
                 'border' : border,
                 'visible' : visible}

class LinePainter(Painter):


    def init(self):
        self.obj.sig_connect('update', self.update)
        
    def update(self, sender, keys):
        
        line, layer_painter = self.obj, self.parent
        layer = layer_painter.obj
        axes, backend = layer_painter.axes, layer_painter.parent

        # visible
        if 'visible' in keys:
            if line.visible is False:
                if layer_painter.line_cache.has_key(line):
                    obj = layer_painter.line_cache.pop(line)
                    if obj in axes.lines:
                        axes.lines.remove(obj)
                self.get_backend().queue_redraw()
                return
                               
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
            raise

        index = layer.lines.index(line)

        # style, layer.group_style
        style = layer.group_style.get(line, index, override=line.style or Undefined)
        global linestyle_mappings
        try:
            style = linestyle_mappings[style]
        except KeyError:
            style = linestyle_mappings.values()[1]

        #:line.marker
        #:layer.group_marker
        marker = layer.group_marker.get(line, index, override=line.marker or Undefined)
        global linemarker_mappings
        try:
            marker = linemarker_mappings[marker]
        except KeyError:
            marker = linemarker_mappings.values()[0]
        
        #:line.width
        #:layer.group_width
        width = layer.group_width.get(line, index, override=line.width or Undefined)
        
        #:line.color
        #:layer.group_color
        color = layer.group_color.get(line, index, override=line.color or Undefined)

        #:line.marker_color
        marker_color = layer.group_marker_color.get(line, index, override=line.marker_color or Undefined)

        #:line.marker_size
        marker_size = line.marker_size or 1

        # When repainting the line, we need to remove the corresponding
        # matplotlib Line object (if it already exists).
        if layer_painter.line_cache.has_key(line):
            obj = layer_painter.line_cache.pop(line)
            if obj in axes.lines:
                axes.lines.remove(obj)
            
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
            layer_painter.line_cache[line] = l
        except Exception, msg:
            raise

        # label
        label = self.get_line_label(line, dataset=ds, cy=cy)
        if label is not None:
            l.set_label(label)            

        self.get_backend().queue_redraw()
        

    def get_line_label(self, line, dataset=None, cy=None):
        label = line.label
        if label is None:
            if dataset is not None and cy is not None:
                info = dataset.get_info(cy)
                label = info.label or dataset.get_name(cy) or None
            else:
                label = line.label
        return label




class LayerPainter(Painter):

    active_line_painter = Instance(LinePainter, init=None)
    line_cache = Dict(keys=Instance(Line))
    
    def init(self):
        self.axes = self.init_axes()
        self.obj.sig_connect('update', self.update)
        self.obj.sig_connect('update::title', self.update_title)

        # updating the axis with start/end = None does not work
        # right now. Somehow the axis is not redrawn at all.
        # Therefore this is a work-around: we simply redraw the
        # complete layer!

        # TODO: can the axis change?
        self.obj.xaxis.sig_connect('update', lambda sender, keys: self.paint())
        self.obj.yaxis.sig_connect('update', lambda sender, keys: self.paint())
        

    def init_axes(self):
        return self.parent.figure.add_subplot('111')


    def update_title(self, sender, new_title):
        # title
        title = new_title
        self.axes.set_title(title or '')

            
    def update(self, sender, keys):

        # plot_painter := backend
        layer, plot_painter = self.obj, self.parent
        axes = self.axes
        
        # title
        if 'title' in keys:
            title = layer.title
            axes.set_title(title or '') # matplotlib doesn't like None as title

        # grid
        if 'grid' in keys:
            axes.grid(layer.grid)

        
        # lines -- these should be updated by update::lines !!!
        for line in layer.lines:
            painter = self.get_painter(line, LinePainter)
            painter.paint()

        # axes
        # This needs to be after lines, because painting the
        # lines would reset the start and end.

#        if 'xaxis' in keys or 'yaxis' in keys:
        self.update_axis(None, [])

        # legend
        # Since the legend labels are constructed from the matplotlib
        # line objects, it is necessary to construct the legend after
        # the lines are plotted
        if 'legend' in keys:
            legend = layer.legend        
            if legend is None:
                # remove any existing legend painter if obsolete
                pass
            else:
                p = self.get_painter(legend, LegendPainter)
                p.paint()
            
        self.get_backend().queue_redraw()

    def update_axis(self, sender, keys):
        
        layer = self.obj
        axes = self.axes
        for (key, axis) in layer.axes.iteritems():
            #:axis.label, :axis.scale, :axis.start,:axis.end
            label, scale, start, end = axis.label, axis.scale, axis.start, axis.end
            logger.debug("Setting range of layer '%s' to [%s:%s], scale is %s" % (label, start, end, scale))            

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

            set_start(start)
            set_end(end)

        self.get_backend().queue_redraw()


    def request_active_line(self):
        """ Return the active line or if it is None, try to set it first. """
        if self.active_line_painter is None:
            if len(self.obj.lines) > 0:
                self.active_line_painter = self.get_painter(self.obj.lines[0], LinePainter)
        return self.active_line_painter.obj

    def set_active_line(self, line):
        """ Set the active_line_painter object to an existing or new
        painter for 'line'."""    
        self.active_line_painter = self.get_painter(line, LinePainter)

#------------------------------------------------------------------------------

class Backend(backend.Backend):

    active_layer_painter = Instance(LayerPainter, init=None)
    
    def init(self):
        self.painters = {} # == layers

        self._redraw = False
        self._block_redraw = 0
        
        self.sig_register('redraw')
        self.sig_connect('redraw', lambda sender: self.redraw())

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

    def get_painter(self, obj, klass=None):
        _id = id(obj)
        try:
            return self.painters[_id]
        except KeyError, msg:
            if klass is not None:
                new_painter = klass(obj, parent=self)
                self.painters[_id] = new_painter
                return new_painter
            else:
                raise       

    def draw(self):
        for layer in self.plot.layers:
            painter = self.get_painter(layer, LayerPainter)
            painter.paint()
        self.canvas.draw()
        self._redraw = False        

    def on_update_layers(self, sender, updateinfo):
        # TODO!!!!
        # check if active layer is still active
        removed = updateinfo.get('removed', [])

        #if self.active_layer in removed:
        #    self.set_active_layer(None)

    def request_active_layer(self):
        """ Return the active layer or if it is None, try to set it first. """
        if self.active_layer_painter is None:
            if len(self.plot.layers) > 0:
                self.active_layer_painter = self.get_painter(self.plot.layers[0])
        return self.active_layer_painter.obj



    def block_redraw(self, count=1):
        self._block_redraw += count

    def unblock_redraw(self, count=1):
        self._block_redraw = max(0, self._block_redraw-count)
        self.redraw()
        
    def queue_redraw(self):
        self._redraw = True
        self.redraw()

    def redraw(self, force=False):
        """ redraw, unlike draw, only redisplays the existing canvas. """
        if force is True or (self._redraw is True and self._block_redraw==0):
            logger.debug("Redraw.")
            self.canvas.draw()
            self._redraw = False
            self._block_redraw = 0
        
        
#------------------------------------------------------------------------------    
globals.BackendRegistry['matplotlib'] = Backend
