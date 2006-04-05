"""
   A complete re-implementation of the Backend mechanism.

   @copyright: 2006, Niklas Volbers <mithrandir42@web.de>
"""


import gtk
import cairo


from Sloppy.Base.objects import SPObject
from Sloppy.Base import objects
from Sloppy.Lib.Check import Instance, List, Dict, Check, Integer


import logging
logger = logging.getLogger('Backends.mpl3')
#------------------------------------------------------------------------------

class Canvas(gtk.DrawingArea, SPObject):

    figure = Instance('Figure')
    
    def __init__(self, **kwargs):
        SPObject.__init__(self, **kwargs)
        gtk.DrawingArea.__init__(self)
        self.connect('expose_event', self.expose)
        
            
    def expose(self, widget, event):
        ctx = widget.window.cairo_create()                   
        
        # set a clip region for the expose event
        ctx.rectangle(event.area.x, event.area.y,
                               event.area.width, event.area.height)
        ctx.clip()
        if isinstance(self.figure, Figure):
            self.figure.draw(ctx)
        
        return False


#------------------------------------------------------------------------------
          
class Artist(SPObject):
    """ Any class that renders some information as graphic is an Artist.

    Currently, I am assuming a 1:1 mapping of data objects and Artist objects.
    The corresponding object is thus accessible via self.
    """

    parent = Check()
    artists = Dict()

    def __init__(self, **kwargs):
        SPObject.__init__(self, **kwargs)

    def get_artist(self, obj):
        _id = id(obj)
        try:
            return self.artists[_id]
        except KeyError:
            print "NEW ARTIST"
            new_artist = ARTISTS[obj.__class__](obj=obj, parent=self)
            self.artists[_id] = new_artist
            return new_artist
        
        
class Figure(Artist):

    obj = Instance(objects.Plot)
    canvas = Instance(Canvas)
    
    def __init__(self, **kwargs):
        Artist.__init__(self, **kwargs)
        self.canvas = Canvas(figure=self)        

    def draw(self, ctx):
        for layer in self.obj.layers:
            a = self.get_artist(layer)
            rect = self.canvas.get_allocation()
            a.width = rect.width - 50
            a.height = rect.height - 50
            a.draw(ctx)
    

    

# Any Artist class starts with A, so that they can easily be distinguished
# from the data objects.

class ALayer(Artist):
    obj = Instance(objects.Layer)
    width = Integer()
    height = Integer()
    
    def draw(self, ctx):
        layer = self.obj
        xaxis = layer.xaxis
        yaxis = layer.yaxis

        ctx.save()
        ctx.set_line_width(10)

        # xaxis
        ctx.move_to(0, 0)
        ctx.rel_line_to(self.width, 0)
        ctx.close_path()        
        ctx.stroke()

        # yaxis
        ctx.move_to(0, 0)
        ctx.rel_line_to(0, self.height)
        ctx.close_path()        
        ctx.stroke()
        
        ctx.restore()
        
        
class ALine(Artist):
    obj = Instance(objects.Line)

    

ARTISTS = {objects.Layer: ALayer}

#------------------------------------------------------------------------------
p = objects.Plot()
p.layers.append(objects.Layer())
fig = Figure(obj=p)

win = gtk.Window()
win.connect('destroy', gtk.main_quit)
win.add(fig.canvas)
win.show_all()
gtk.main()

