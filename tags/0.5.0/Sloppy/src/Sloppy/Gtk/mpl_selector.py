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
`Selector` objects allow the user to pick a point/region/line or
anything else, providing a visual clue (e.g. a statusbar message,
a rectangle or a line, ...).
"""


import gtk
import gobject

import math

from Sloppy.Lib.Signals import HasSignals


#------------------------------------------------------------------------------
# Constants

SELECTLINE_VERTICAL = 1
SELECTLINE_HORIZONTAL = 2
SELECTLINE_CROSSHAIR = 3  # both of the above



#------------------------------------------------------------------------------
# Helper Methods


def confine_to_bbox(x, y, bbox):
    x = min(max(bbox.xmin(), x), bbox.xmax())
    y = min(max(bbox.ymin(), y), bbox.ymax())
    return (int(x), int(y))


def int_tuple(*args):
    " Returns a tuple with the arguments converted to integer. "
    rv = list()
    for arg in args:
        rv.append( int(arg) )
    return tuple(rv)



def nearest_match(trans, x, y, xdata, ydata):

    """
    With 'nearest' we mean 'nearest on the screen', so we need
    to compare the given x,y position with the x/y position of
    each data point (xdata[n], ydata[n]).
    This tuple is calculated using the given transformation 'trans',
    which can be retrieved via self.axes.transData
    """

    if len(xdata) == 0:
        return None, None

    # calculate difference to other point
    def dist(x1, y1, x2, y2):
        return (x1-x2)**2 + (y1-y2)**2

    # delta is the smallest yet encountered difference
    delta = dist(x, y, *trans.xy_tup((xdata[0], ydata[0])))
    index = 0

    n=0
    for xv in xdata:
        d = dist(x, y, *trans.xy_tup((xv, ydata[n])))
        if d < delta:
            index = n
            delta = d
        n += 1

    return (index, delta)    



    
def draw_crosshair(self, gc, x, y, size=5):
    " Draw a crosshair at the given position. "
    self.draw_line(gc, x-size, y, x+size, y)
    self.draw_line(gc, x, y-size, x, y+size)
           


#------------------------------------------------------------------------------
# Base Selector Class

class Selector(HasSignals):
    
    " Base class for any Selector. "

    def __init__(self, figure, axes=None):
        self.figure = figure
        self.canvas = figure.canvas
        self.axes = axes
        self._mpl_events = {}

        HasSignals.__init__(self)
        self.sig_register("aborted")
        self.sig_register("finished")
        
    
    def init(self):
        pass
    

    def finish(self, abort=False):
        self.mpl_disconnect_all()
        if abort is True:
            self.sig_emit("aborted")
        else:
            self.sig_emit("finished")


    def abort(self):
        self.finish(abort=True)


    def mpl_connect(self, s, cb):
        self._mpl_events[s] = self.canvas.mpl_connect(s, cb)


    def mpl_disconnect(self, s):
        self.canvas.mpl_disconnect( self._mpl_events.pop(s) )


    def mpl_disconnect_all(self):
        for event in self._mpl_events.itervalues():
            self.canvas.mpl_disconnect(event)



class BufferedRedraw:

    def __init__(self):
        self._imageBack = None
        self._idleId = 0
        
    def buffered_redraw(self, func=None, *args):

        if self.axes is None:
            return
        
        drawable = self.canvas.window
        if drawable == None: return
        gc = drawable.new_gc()

        # There is no guarantee that the canvas size stays constant
        # during the selection.  E.g. the user might resize the window.
        # We check for this by comparing the size of the saved image
        # to the new canvas size.  If it doesn't match, then we
        # need to refresh the image.
        fig_height = self.canvas.figure.bbox.height()
        l,b,w,h = [int(val) for val in self.axes.bbox.get_bounds()]
        axrect = int_tuple(l,fig_height-(b+h),l+w,fig_height-b)
        if self._imageBack is not None:
            lastrect, imageBack = self._imageBack

        if self._imageBack is None or axrect != lastrect:
            # 'axrect' is a rectangle in screen coordinates that delimits
            # the axes that we are drawing in.  The y coordinates are flipped
            # due to different origins of the coordinate systems.
            self._imageBack = axrect, drawable.get_image(*axrect)
            self._idleId = 0

        lastrect, imageBack = self._imageBack
        def idle_draw(*args):
            drawable.draw_image(gc, imageBack, 0, 0, *lastrect)
            if func is not None:
                func(drawable, gc)
            self._idleId = 0
            return False
        if self._idleId==0:
            self._idleId = gobject.idle_add(idle_draw)



#------------------------------------------------------------------------------
# Selector Implementations

class Cursor( Selector ):

    def __init__(self, figure, axes=None):
        Selector.__init__(self, figure, axes)
        self.sig_register('move')
        
    def init(self):
        self.mpl_connect('motion_notify_event', self.mouse_move)

    def mouse_move(self, event):
        if not event.inaxes:
            return 
        ax = event.inaxes
        minx, maxx = ax.get_xlim()
        miny, maxy = ax.get_ylim()

        x, y = event.xdata, event.ydata
        self.sig_emit("move", x, y)



class ObjectPicker( Selector ):

    def init(self):
        self.mpl_connect('button_press_event', self.button_press)
        self.sig_register('picked-axes')
        
    def button_press(self, event):
        ax = event.inaxes
       
        if event.button == 3:
            self.sig_emit("picked-axes", ax)
                
        elif event.button == 1:
            if ax is not None:
                obj = ax.pick(event.x, event.y)
            else:
                obj = None
            print "RMB, you picked", obj




class SelectPoint( Cursor ):

    def __init__(self, figure, button=1):
        Selector.__init__(self, figure=figure)

        self.button = button
        self.point = None  # return value

        self.sig_register("newcoords")

    def init(self):
        self.mpl_connect('button_press_event', self.button_press)
        self.mpl_connect('motion_notify_event', self.mouse_move)        


    def finish(self, abort=False):
        self.statusbar.pop(self.context_id)        
        Cursor.finish(self, abort=abort)


    def mouse_move(self, event):
        if not event.inaxes:
            return 
        ax = event.inaxes
        minx, maxx = ax.get_xlim()
        miny, maxy = ax.get_ylim()

        x, y = event.xdata, event.ydata
        self.sig_emit("newcoords", x, y)

        # return value
        self.point = (x, y)


    def button_press(self, event):
        if event.button == self.button:
            self.finish()



        
class SelectRegion( Selector, BufferedRedraw ):

    """    
    Selector that allows to choose a (rectangular) region by clicking
    on a position and then dragging the mouse to the second position.
    The current selection is indicated by a dashed rectangle.
    """
    
    def __init__(self, figure, axes=None, button=1):
        """
        @param figure: Figure object to use.
        
        @param axes: Axes object.  If None, the axes are automatically
          determined from the mouse position on the first mouse click.

        @button: Mouse button that starts the selection.          
        """
        
        Selector.__init__(self, figure=figure, axes=axes)
        BufferedRedraw.__init__(self)
              
        self.x0, self.y0 = 0,0
        self.x1, self.y1 = 0,0

        self.xdata0, self.ydata0 = 0,0
        self.xdata1, self.ydata1 = 0,0

        self.cursor = gtk.gdk.Cursor(gtk.gdk.TCROSS)
        self.button = button

        self._rect = None

        self.region = None  # return value
        

    def init(self):
        self.canvas.window.set_cursor(self.cursor)        
        self.mpl_connect("button_press_event", self.on_button_press)


    def finish(self, abort=False):
        self.canvas.window.set_cursor(None)
        self._imageBack = None
        self.canvas.draw()

        self.region = (self.xdata0, self.ydata0, self.xdata1, self.ydata1)
        Selector.finish(self, abort=abort)

            
    def on_button_press(self, event):
        # self.axes may not yet be set after 'init'.  In that
        # case, we will determine the axes from the mouse coordinates.
        if self.axes is None:
            if event.inaxes is None:
                return
            else:
                self.axes = event.inaxes
        ax = self.axes

        if event.button == self.button and event.inaxes is ax:
            self.mpl_connect('motion_notify_event', self.on_motion_notify)
            
            # remember starting position
            height = self.canvas.figure.bbox.height()
            self.x0, self.y0 = event.x, height - event.y
            self.x1, self.y1 = self.x0, self.y0

            self.xdata0 = self.xdata1 = event.xdata
            self.ydata0 = self.ydata1 = event.ydata

            self.mpl_connect('button_release_event', self.on_button_release)
        

    def on_button_release(self, event):

        xdata0 = min(self.xdata0, self.xdata1)
        xdata1 = max(self.xdata0, self.xdata1)
        ydata0 = min(self.ydata0, self.ydata1)
        ydata1 = max(self.ydata0, self.ydata1)

        self.xdata0 = xdata0 ; self.ydata0 = ydata0
        self.xdata1 = xdata1 ; self.ydata1 = ydata1
               
        self.finish()
            
        
    def on_motion_notify(self, event):        

        # current pixel position
        self.x1, self.y1 = confine_to_bbox(event.x, event.y, self.axes.bbox)
        
        # calculate data from this position
        def transform(x,y):
            return self.axes.transData.inverse_xy_tup((x, y))
        self.xdata1, self.ydata1 = transform(self.x1, self.y1)

        # y coordinates are flipped relative to screen position,
        # so we transform them.
        height = self.canvas.figure.bbox.height()
        self.y1 = height - self.y1
        
        w = abs(self.x1 - self.x0)
        h = abs(self.y1 - self.y0)
        
        self._rect = [int(val) for val in min(self.x0,self.x1), min(self.y0, self.y1), w, h]


        def draw_rectangle(drawable, gc):
            gc.line_style = gtk.gdk.LINE_ON_OFF_DASH            
            drawable.draw_rectangle(gc, False, *self._rect)
            
        self.buffered_redraw(draw_rectangle)



class SelectLine(Selector, BufferedRedraw):

    """    
    Selector that follows mouse movement with a vertical, a horizontal
    line or with both.  This allows the user to select only an x or a
    y value or in the last case to easily select a point.

    Note that once the Selector is started, there is no need for the
    user to click with the mouse.  The line position automatically
    follows the user's movements and a mouse click indicates that a
    point is selected.    
    """
    
    def __init__(self, figure, axes=None, mode=SELECTLINE_VERTICAL):
        """        
        @param figure: Figure object.
        
        @param axes: Axes object.  If None, the axes are automatically
          determined on the first motion_notify event.  This is useful
          if you enable the Selector while the mouse is already on the
          graph.

        @param mode: One of SELECTLINE_xxx.        
        """
        
        Selector.__init__(self, figure=figure, axes=axes)
        BufferedRedraw.__init__(self)
        
        self.mode = mode

        # coordinates to draw lines in draw_idle
        self._lines = None
                
        self.line = None # return value
        
        
    def init(self):
        self.mpl_connect("button_press_event", self.on_button_press)
        self.mpl_connect('motion_notify_event', self.on_motion_notify_event)
        
        
    def on_button_press(self, event):
        if event.inaxes is self.axes:
            self.finish()
            

    def finish(self, abort=False):
        self._imageBack = None
        self.canvas.draw()            
        Selector.finish(self, abort=abort)

        
    def on_motion_notify_event(self, event):
        # self.axes may not yet be set after 'init'.  In that
        # case, we will set it to the first axes that we hover over.       
        if self.axes is None:
            if event.inaxes is None:
                return
            else:
                self.axes = event.inaxes
        ax = self.axes
        
        drawable = self.canvas.window
        if drawable == None: return
        gc = drawable.new_gc()
        gc.line_style = gtk.gdk.LINE_ON_OFF_DASH

        x, y = confine_to_bbox(event.x, event.y, self.axes.bbox)
        l, b, w, h = [int(val) for val in ax.bbox.get_bounds()]

        fig_height = int(self.canvas.figure.bbox.height())

        # add lines depending on selector mode
        self._lines = list()
        if self.mode & SELECTLINE_VERTICAL:
            self._lines.append( int_tuple(x, fig_height-b, x, fig_height-(b+h)) )
        if self.mode & SELECTLINE_HORIZONTAL:
            self._lines.append( int_tuple(l, fig_height-y, l+w, fig_height-y) )

        def draw_lines(drawable, gc):
            for line in self._lines:
                drawable.draw_line(gc, *line)
            
        self.buffered_redraw(draw_lines)

        # set return value
        self.line = event.xdata, event.ydata



class ChangeViewRegion(Selector):

    " Base class for any Selector that changes the viewed region. "
    
    def __init__(self, figure, axes=None):
        """        
        @param figure: Figure object.
        
        @param axes: Axes object.  If None, the axes are automatically
          determined from the mouse position on the first mouse click.
        """
        
        Selector.__init__(self, figure, axes)

        self.cursor = gtk.gdk.Cursor(gtk.gdk.FLEUR)
        self._imageBack = None
        
        self.x, self.y = 0,0
        
        # self.xmin is set to None to indicate that it has not yet been set
        self.xmin, self.xmax, self.ymin, self.ymax = None,0,0,0

        self._idleId = 0

        self.region = None  # return value
        
    def init(self):
        self.canvas.window.set_cursor(self.cursor)

        # If no axes has been specified in __init__, then the
        # axes is determined from the first user mouse click.
        self.mpl_connect("button_press_event", self.on_button_press)

        
    def finish(self, abort=False):
        self.canvas.window.set_cursor(None)
        if abort is True and self.axes is not None and self.xmin is not None:
            # restore original position
            self.axes.set_xlim((self.xmin, self.xmax))
            self.axes.set_ylim((self.ymin, self.ymax))
            self.canvas.draw()
            
        Selector.finish(self, abort=abort)

        
    def on_button_press(self, event):

        # self.axes may not yet be set after 'init'.  In that
        # case, we will determine the axes from the mouse coordinates.
        if self.axes is None:
            self.axes = event.inaxes

        if not self.axes or event.inaxes != self.axes:
            return

        self.mpl_disconnect("button_press_event")    
        self.mpl_connect("button_release_event", self.on_button_release)
        self.mpl_connect("motion_notify_event", self.on_motion_notify_event)

        self.x, self.y = event.x, event.y
        self.width = self.axes.bbox.width()
        self.height = self.axes.bbox.height()

        # data limits
        self.xmin, self.xmax = self.axes.get_xlim()
        self.ymin, self.ymax = self.axes.get_ylim()

        # steps per pixel
        self.stepx = (self.xmax - self.xmin) / self.width
        self.stepy = (self.ymax - self.ymin) / self.height

        # only for logarithmic scale
        # dppy = decades per pixel (for base 10) in y-direction
        # dppx accordingly for x-direction
        if self.axes.get_yscale() == 'log':
            self.dppy = math.log(self.ymax/self.ymin, 10)/self.height
        if self.axes.get_xscale() == 'log':            
            self.dppx = math.log(self.xmax/self.xmin, 10)/self.width


    def on_button_release(self, event):
        self.finish()
        

    def on_motion_notify_event(self, event):

        self.region = (xmin, ymin, xmax, ymax) = self.calculate_region(event)
                   
        # set new position
        self.axes.set_xlim((xmin, xmax))
        self.axes.set_ylim((ymin, ymax))       

        # add redraw if idle        
        def idle_draw(*args):
            self.canvas.draw()
            self._idleId = 0
            return False        

        if self._idleId==0:
            self._idleId = gobject.idle_add(idle_draw)




class MoveAxes( ChangeViewRegion ):

    """
    Selector to shift the start and end range of an Axes object.
    Note that logarithmic plots are supported!
    """
    
    def calculate_region(self, event):
                
        x, y = event.x, event.y
        
        # the offset is calculated relative to the click-position as
        # determined in 'on_button_press'
        dx = x - self.x
        dy = y - self.y
        
        xmin, xmax = self.xmin, self.xmax
        xscale = self.axes.get_xscale()
        if xscale == 'linear':
            dx = dx * self.stepx
            xmin -= dx
            xmax -= dx               
        elif xscale == 'log':
            dx *= self.dppx
            xmin /= 10**dx
            xmax /= 10**dx
        else:
            raise KeyError("Unknown x-scale %s" % xscale)

        ymin, ymax = self.ymin, self.ymax
        yscale = self.axes.get_yscale()
        if yscale == 'linear':
            dy = dy * self.stepy
            ymin -= dy
            ymax -= dy               
        elif yscale == 'log':
            dy *= self.dppy            
            ymin /= 10**dy
            ymax /= 10**dy
        else:
            raise KeyError("Unknown y-scale %s" % yscale)

        return (xmin, ymin, xmax, ymax)
    



class ZoomAxes(ChangeViewRegion):

    """
    Selector that allows zooming in and out by clicking on an Axes
    and then dragging the mouse.
    """
    
    def __init__(self, figure, axes=None, acceleration=0.5):
        """        
        @param figure: Figure object.
        
        @param axes: Axes object.  If None, the axes are automatically
          determined from the mouse position on the first mouse click.

        @acceleration: value that determines how much each mouse
          movement will zoom into/or out of the axes. A positive value
          indicates zooming out, a negative value zooming in.
        """
        
        ChangeViewRegion.__init__(self, figure, axes)
        self.acceleration = acceleration
        
    def calculate_region(self, event):

        #x, y = confine_to_bbox(event.x, event.y, self.axes.bbox)
        x, y = event.x, event.y
        
        dx = self.acceleration * math.sqrt((x-self.x)**2)
        dy = self.acceleration * math.sqrt((y-self.y)**2)
        
        xmin, xmax = self.xmin, self.xmax

        xscale = self.axes.get_xscale()
        if xscale == 'linear':
            dx = dx * self.stepx
            xmin -= dx
            xmax += dx
        elif xscale == 'log':
            dx *= self.dppx            
            xmin /= 10**dx
            xmax *= 10**dx
        else:
            raise KeyError("Unknown x-scale %s" % xscale)

        ymin, ymax = self.ymin, self.ymax
        yscale = self.axes.get_yscale()
        if yscale == 'linear':
            dy = dy * self.stepy
            ymin -= dy
            ymax += dy               
        elif yscale == 'log':
            dy *= self.dppy
            ymin /= 10**dy
            ymax *= 10**dy
        else:
            raise KeyError("Unknown y-scale %s" % yscale)

        return (xmin, ymin, xmax, ymax)

      


class DataCursor( Cursor, BufferedRedraw ):

    """
    Selector that tries to set a crosshair cursor at the data point
    that is closest to the user's mouse clicks.  The data point is
    determined from all visible lines. Logarithmic axes are supported.

    Once the cursor has been set on a line, it is possible to move this
    cursor with the cursor keys or alternatively using 'j' and 'k'.
    Pressing 'shift' will accelerate the movement.
    """
    
    def __init__(self, figure, axes=None):
        """        
        @param figure: Figure object.
        
        @param axes: Axes object.  If None, the axes are automatically
          determined from the mouse position on the first mouse click.
        """
        
        Selector.__init__(self, figure, axes)
        BufferedRedraw.__init__(self)
        
        self.index = -1
        self.factor = 1 # speed of movement
        self.line = None
        self.bounds = None
        self.coords = None
        
        self._imageBack = None
        
        self.point = None  # return value

        self.sig_register("update-position")

    def init(self):
        self.mpl_connect('button_press_event', self.button_press_event)
        self.mpl_connect('motion_notify_event', self.mouse_move)
        self.canvas.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.TCROSS))


    def finish(self, abort=False):
        self.canvas.window.set_cursor(None)
        self.buffered_redraw()
        Cursor.finish(self, abort=abort)


    def key_press_event(self, event):
       
        if event.key == 'left' or event.key == 'j':
            self.set_new_index(self.index-self.factor)
        elif event.key == 'right' or event.key == 'k':
            self.set_new_index(self.index+self.factor)
        elif event.key == 'shift':
            self.factor = 5
        elif event.key == ' ':
            self.finish()
        else:
            return


    def key_release_event(self, event):
        if event.key == 'shift':
            self.factor = 1
            

    def set_new_index(self, index):
        " Sets the new index (but keeps the line). "

        if index >= self.bounds[0] and index <= self.bounds[1]:
            self.index = index

            xdata = self.line.get_xdata()[index]
            ydata = self.line.get_ydata()[index]
            self.point = (xdata, ydata)
            
            self.coords = self.axes.transData.xy_tup((xdata,ydata))

            self.sig_emit("update-position", self.line, self.index, self.point)
            self.draw()
            

    def button_press_event(self, event):
        if event.button != 1 or event.inaxes is None:
            return

        if self.axes is not None and self.axes != event.inaxes:
            return
        else:      
            self.axes = event.inaxes
                
        def transform(x,y):
            return self.axes.transData.inverse_xy_tup((x, y))
        self.point = transform(event.x, event.y)
        
        # If this was the first click, then connect to key events
        if self.index == -1:
            self.mpl_connect('key_press_event', self.key_press_event)
            self.mpl_connect('key_release_event', self.key_release_event)

        self.determine_line_index( (event.x, event.y) )

        self.canvas.grab_focus()


    def determine_line_index(self, point):

        x, y = point

        # Now find the corresponding x,y pair in the dataset
        # that matches best!

        last_match = None
        
        lines = self.axes.lines
        for line in lines:
            xdata = line.get_xdata()
            ydata = line.get_ydata()

            index, delta = nearest_match(self.axes.transData, x, y, xdata, ydata)
            if index is not None and \
                   (last_match is None or last_match[2] > delta):
                last_match = line, index, delta            

        # TODO: self.bounds is determined by the length of the data.
        # TODO: This is ok, but we might need to refine this, once we use
        # TODO: matplotlib's facility to clip the lines.
        self.line = last_match[0]
        self.bounds = (0, max(0, len(self.line.get_xdata())-1))
        self.set_new_index(last_match[1])
    
        
    def draw(self):

        def do_draw(drawable, gc):
            if self.axes.bbox.contains(*self.coords) == 0:
                return
                
            fig_height = self.canvas.figure.bbox.height()
            x, y = self.coords
            x, y = int(x), int(fig_height-y)
            draw_crosshair(drawable, gc, x, y)
            
        self.buffered_redraw(do_draw)




        
