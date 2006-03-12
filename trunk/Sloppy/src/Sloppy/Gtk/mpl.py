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


import gtk, gobject
from matplotlib.backends.backend_gtk import FileChooserDialog

import uihelper, mpl_selector
from Sloppy.Base import uwrap, globals
from Sloppy.Lib.Undo import UndoList, NullUndo, ulist, UndoInfo


#     def disable_interaction(self, widget):
#         " Disable most user interaction. "        
#         actiongroups = self.uimanager.get_action_groups()
#         for actiongroup in actiongroups:
#             if actiongroup.get_name() in ['ViewMenu']:
#                 continue
#             if actiongroup.get_sensitive() is True:
#                 actiongroup.set_sensitive(False)
#                 self.disabled_groups.append(actiongroup)               

#     def enable_interaction(self, widget):
#         " Re-enable all interaction disabled by disable_interaction. "
#         for actiongroup in self.disabled_groups:
#             actiongroup.set_sensitive(True)
#         self.disabled_groups = list()

# To enable mplwidget ui:
#  add actiongroups to uimanager
#  merge ui string

# To disable mplwidget ui
#  remove actiongroups
#  unmerge ui via merge id



class MatplotlibWidget(gtk.VBox):

    __gsignals__ = {
        'edit-mode-started' : (gobject.SIGNAL_RUN_FIRST , gobject.TYPE_NONE, ()),
        'edit-mode-ended' : (gobject.SIGNAL_RUN_FIRST , gobject.TYPE_NONE, ())        
        }

    
    actions_dict = {
        'Plot':
        [
        ('PlotMenu', None, '_Plot'),
        ('Replot', 'sloppy-replot', '_Replot', '<control>R', 'Replot', 'on_action_Replot'),
        ('ExportViaMPL', gtk.STOCK_SAVE_AS, 'Export via matplotlib...', None, 'Export via Matplotlib', 'on_action_ExportViaMPL'),
        ('ExportViaGnuplot', gtk.STOCK_SAVE_AS, 'Export via gnuplot...', None, 'Export via Gnuplot', 'on_action_ExportViaGnuplot'),
        ],
        'Analysis':
        [
        ('AnalysisMenu', None, '_Analysis')
        ],
        'Display':
        [
        ('DisplayMenu', None, '_Display'),
        ('ZoomIn', gtk.STOCK_ZOOM_IN, '_Zoom In', 'plus', 'Zoom', 'on_action_ZoomIn'),
        ('ZoomOut', gtk.STOCK_ZOOM_OUT, '_Zoom Out', 'minus', 'Zoom', 'on_action_ZoomOut'),
        ('ZoomFit', gtk.STOCK_ZOOM_FIT, '_Zoom Fit', '0', 'Zoom', 'on_action_ZoomFit'),
        ('ZoomRect', gtk.STOCK_ZOOM_FIT, '_Zoom Rectangle', 'r', 'Zoom', 'on_action_ZoomRect'),
        ('MoveAxes', None, 'Move Plot', 'm', '', 'on_action_MoveAxes'),
        ('DataCursor', None, 'Data Cursor', 'c', '', 'on_action_DataCursor'),
        ('SelectLine', None, 'Select Line', 's', '', 'on_action_SelectLine'),
        ('ZoomAxes', None, 'Zoom Axes', 'z', '', 'on_action_ZoomAxes')
        ]
        }


    def __init__(self, project, plot):
        gtk.VBox.__init__(self)

        self._current_selector = None

        # construct action groups
        actiongroups = list()
        for key, actions in self.actions_dict.iteritems():
            ag = gtk.ActionGroup(key)
            ag.add_actions( uihelper.map_actions(actions, self) )
            actiongroups.append(ag)
        self.actiongroups = actiongroups
        
        ### statusbar
        self.statusbar = globals.app.window.statusbar
        ##self.statusbar = gtk.Statusbar()
        ##self.statusbar.show()

        # coords
        self.coords = gtk.Label()
        self.coords.show()
        
        self.context_id = self.statusbar.get_context_id("coordinates")
        #self.statusbar.push(self.context_id, "X: 10, Y: 20")
        #self.statusbar.pop(self.context_id)
        
        vbox = self.vbox = gtk.VBox()
        hbox = gtk.HBox()
        ##hbox.pack_start(self.btn_cancel, False, padding=4)
        hbox.pack_start(self.coords, False, padding=4)
        ##hbox.pack_start(self.statusbar, padding=4)
        hbox.show()
        vbox.pack_end(hbox, False, True)
        vbox.show()

        self.add(vbox)

        # set up project/plot
        self.project = project        
        self.plot = None
        self.backend = None
        self.cursor = None

        self._signals = []
        self.cblist = []

        self.set_plot(plot)
        self.project.sig_connect("close", (lambda sender: self.destroy()))

        # set up file selector for export dialog
        # TODO: this could be put into a plugin, since it is desirable to have
        # TODO: such a method in the shell frontend as well.
        self.fileselect = FileChooserDialog(title='Save the figure', parent=None)


    def get_actiongroups(self):
        return self.actiongroups

    def get_uistring(self):
        return globals.app.get_uistring('plot-widget')
    
    #----------------------------------------------------------------------
    def set_coords(self, x, y):
        if x is not None and y is not None:
            self.coords.set_text("X: %1.2f, Y: %1.2f" % (x,y))
        else:
            self.coords.set_text("invalid coordinates")
        
    def set_plot(self, plot):
        # TODO: remove old plot
        # TODO: connect to plot's title    

        if plot is not None:
            backend = self.project.request_backend('matplotlib', plot=plot)

            # TODO: set canvas size depending on outer settings, on dpi
            # TODO: and zoom level

            # minium canvas size
            canvas_width, canvas_height = 320,240
            backend.canvas.set_size_request(canvas_width, canvas_height)

            # [NV] I disabled rulers again to get ready for the next release.
            if False:
                # add rulers
                hruler = gtk.HRuler()
                hruler.set_metric(gtk.PIXELS)
                hruler.set_range(0, canvas_width, 0, canvas_width)

                vruler = gtk.VRuler()
                vruler.set_metric(gtk.PIXELS) # gtk.INCHES, gtk.CENTIMETERS
                vruler.set_range(0, canvas_height, 0, canvas_height)

                # motion notification
                def motion_notify(ruler, event):
                    return ruler.emit("motion_notify_event", event)
                #backend.canvas.connect_object("motion_notify_event", motion_notify, ruler)

                # put scrollbars around canvas
                scrolled_window = gtk.ScrolledWindow()
                scrolled_window.add_with_viewport(backend.canvas)
            
                # the layout is done using a table
                layout = gtk.Table(rows=3, columns=2)
                layout.attach(hruler, 1, 2, 0, 1, gtk.EXPAND|gtk.SHRINK|gtk.FILL, gtk.FILL)
                layout.attach(vruler, 0, 1, 1, 2, gtk.FILL, gtk.EXPAND|gtk.SHRINK|gtk.FILL)
                layout.attach(scrolled_window, 1, 2, 1, 2, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
            else:
                layout = backend.canvas
                
            layout.show_all()
            self.vbox.pack_start(layout)
            
            # add scrollbar
            #sw = uihelper.add_scrollbars(backend.canvas, viewport=True)
            #sw.show()            
            #self.vbox.pack_start(sw)
        else:
            backend = None
           
        # disconnect old stuff
        if self.backend is not None and self.backend != backend:
            self.backend.disconnect()

        for cb in self.cblist:
            cb.disconnect()
        self.cblist = []
        
        if self.cursor is not None:
            self.cursor.finish()

        # connect new backend
        self.plot = plot
        self.backend = backend


        if backend is not None:
            self.cblist += [
                plot.sig_connect("changed", (lambda sender: backend.draw())),
                plot.sig_connect("closed", (lambda sender: self.destroy())),
                backend.sig_connect("closed", (lambda sender: self.destroy()))
                ]
            
            try:
                backend.draw()
            except:
                raise            

            # Cursor
            self.cursor = mpl_selector.Cursor(self.backend.figure)
            self.cursor.sig_connect("move", (lambda sender,x,y: self.set_coords(x,y)))
            self.cursor.init()


    def request_active_layer(self):
        layer = self.backend.request_active_layer()
        if layer is not None:
            return layer
        else:
            globals.app.err_msg("No active layer!")
            raise UserCancel
    
        
    #----------------------------------------------------------------------
    def on_action_Replot(self, action):
        self.backend.draw()
        
    #----------------------------------------------------------------------

    def zoom_to_region(self, layer, region, undolist=[]):

        old_region = (layer.xaxis.start,
                      layer.yaxis.start,
                      layer.xaxis.end,
                      layer.yaxis.end)
        
        x0 = min( region[0], region[2] )
        x1 = max( region[0], region[2] )            
        y0 = min( region[1], region[3] )
        y1 = max( region[1], region[3] )

        # Do not zoom if x0 == x1 or if y0 == y1, because
        # otherwise matplotlib will mess up.  Of course, if x0 and
        # x1 are None (or y0 and y1), i.e. if autoscale is turned on,
        # then it is ok to zoom.
        if ((x0 is not None) and (x0 == x1)) or \
           ((y0 is not None) and (y0 == y1)):            
            undolist.append(NullUndo())
            return

        def set_axis(axis, start, end):
            if axis.start is not None and axis.end is not None:
                swap_axes = axis.start > axis.end
            else:
                swap_axes = False

            if swap_axes is True:
                _start, _end = end, start
            else:
                _start, _end = start, end

            axis.start = _start
            axis.end = _end            

        # TODO:
        # This emits a signal update::start and update::end
        # for each manipulated axis. We might need an AxisPainter,
        # then the notification makes sense. However, since we
        # don't want to force two redraws, we might be able to
        # block one of the signals and force a complete redraw
        # of the axis.
        # TODO: block signals update::xxx for layer
        set_axis(layer.xaxis, x0, x1)
        set_axis(layer.yaxis, y0, y1)
        layer.sig_emit('update', '__all__', None)

        ui = UndoInfo(self.zoom_to_region, layer, old_region).describe("Zoom Region")
        undolist.append(ui)

    def axes_from_xy(self, x, y):
        " x,y should be plot coordinates, not screen coordinates. "
        for layer in self.plot.layers:
            axes = self.backend.layer_to_axes[layer]
            if axes.bbox.contains(x,y) == 1:
                return axes
        else:
            return None

    # might be used in ZoomSelector as well
    # => either static method or put it somewhere else
    def calculate_zoom_region(self, axes, dx=0.1, dy=0.1):
        xmin, xmax = axes.get_xlim()
        width = (xmax-xmin)
        if axes.get_xscale() == 'log':
            alphax = pow(10.0, dx)
            xmin *= alphax
            xmax /= alphax
        else: # linear
            xmin += width*dx
            xmax -= width*dx

        ymin, ymax = axes.get_ylim()
        height = ymax-ymin
        if axes.get_yscale() == 'log':
            alphay = pow(10.0, dy)
            ymin *= alphay
            ymax /= alphay
        else: # linear
            ymin += height*dy
            ymax -= height*dy

        return (xmin, ymin, xmax, ymax)


    #------------------------------------------------------------------------------

    def on_action_ZoomRect(self, action):

        def finish_zooming(sender):
            self.statusbar.pop(self.statusbar.get_context_id('action-zoom'))
            ul = UndoList().describe("Zoom Region")
            layer = self.backend.active_layer
            self.zoom_to_region(layer, sender.region, undolist=ul)
            self.project.journal.add_undo(ul)

        layer = self.request_active_layer()
        axes = self.backend.get_painter(layer).axes
        s = mpl_selector.SelectRegion(self.backend.figure, axes=axes)
        s.sig_connect('finished', finish_zooming)
        self.statusbar.push(self.statusbar.get_context_id('action-zoom'),
                            "Use the left mouse button to zoom.")
        self.select(s)

    def on_action_ZoomFit(self, action):
        self.abort_selection()
        layer = self.request_active_layer()
        if layer is not None:
            region = (None,None,None,None)
            self.zoom_to_region(layer, region, undolist=globals.app.project.journal)
    
    def on_action_ZoomIn(self, action):
        self.abort_selection()
        layer = self.request_active_layer()
        if layer is not None:
            axes = self.backend.get_painter(layer).axes
            region = self.calculate_zoom_region(axes)
            self.zoom_to_region(layer, region, undolist=globals.app.project.journal)
        
    def on_action_ZoomOut(self, action):
        self.abort_selection()
        layer = self.request_active_layer()
        if layer is not None:
            axes = self.backend.get_painter(layer).axes
            region = self.calculate_zoom_region(axes, dx=-0.1, dy=-0.1)
            self.zoom_to_region(layer, region, undolist=globals.app.project.journal)

    def on_action_MoveAxes(self, action):

        def finish_moving(sender):
            ul = UndoList().describe("Move Graph")
            layer = self.backend.active_layer#axes_to_layer[sender.axes]
            self.zoom_to_region(layer, sender.region, undolist=ul)
            self.project.journal.add_undo(ul)           

        layer = self.request_active_layer()
        axes = self.backend.get_painter(layer).axes
        s = mpl_selector.MoveAxes(self.backend.figure, axes)
        s.sig_connect("finished", finish_moving)
        self.select(s)
        

    def on_action_DataCursor(self, action):
        layer = self.request_active_layer()
        axes = self.backend.get_painter(layer).axes
        s = mpl_selector.DataCursor(self.backend.figure, axes)

        def abort_selector(sender):
            context_id = self.statusbar.get_context_id("data_cursor")            
            self.statusbar.pop(context_id)
            
        def finish_selector(sender):
            context_id = self.statusbar.get_context_id("data_cursor")            
            self.statusbar.pop(context_id)
            xvalue, yvalue = sender.point

        def update_position(sender, line, index, point):
            # Note that 'line' is a Line2d instance from matplotlib!
            x, y = point
            context_id = self.statusbar.get_context_id("data_cursor")            
            self.statusbar.pop(context_id)
            self.statusbar.push(context_id, "X: %f, Y: %f (value #%s)" %
                                (x, y, index))

        context_id = self.statusbar.get_context_id("data_cursor")
        s.sig_connect("update-position", update_position)
        s.sig_connect("finished", finish_selector)
        s.sig_connect("aborted", abort_selector)             
        self.select(s)


    def on_action_SelectLine(self, action):
            
        def finish_select_line(sender):
            print "FINISHED SELECT LINE", sender.line

        layer = self.request_active_layer()
        axes = self.backend.get_painter(layer).axes
        s = mpl_selector.SelectLine(self.backend.figure, axes,
                                    mode=mpl_selector.SELECTLINE_VERTICAL)
        s.sig_connect("finished", finish_select_line)        
        self.select(s)


    def on_action_ZoomAxes(self, action):

        def finish_moving(sender):
            ul = UndoList().describe("Zoom Axes")
            layer = self.backend.active_layer#axes_to_layer[sender.axes]
            self.zoom_to_region(layer, sender.region, undolist=ul)
            self.project.journal.add_undo(ul)           

        layer = self.request_active_layer()
        axes = self.backend.get_painter(layer).axes
        s = mpl_selector.ZoomAxes(self.backend.figure, axes)
        s.sig_connect("finished", finish_moving)
        self.select(s)
        
        
    #----------------------------------------------------------------------
    def abort_selection(self):
        if self._current_selector is not None:
            self._current_selector.abort()
            self._current_selector = None

        for ag in self.get_actiongroups():
            ag.set_sensitive(True)

        globals.app.sig_emit('end-user-action')

    def select(self, selector):
        self.emit("edit-mode-started")
        self._current_selector = None
            
        def on_finish(sender):            
            # Be careful not to call self.abort_selection() in this place.
            print "---"
            print "FINISHING"            
            self._current_selector = None
            globals.app.sig_emit('end-user-action')
            self.emit("edit-mode-ended")

        globals.app.sig_emit('begin-user-action', on_finish)
        selector.sig_connect("finished", on_finish)
        selector.sig_connect("aborted", on_finish)
        self._current_selector = selector
        selector.init()


   #----------------------------------------------------------------------
   # other callbacks

   
    def on_action_ExportViaMPL(self, action):
        self.abort_selection()

        # TODO: pick filename based on self.get_plot().key
        fname = self.fileselect.get_filename_from_user()
        if fname is not None:
            self.backend.canvas.print_figure(fname)


    def on_action_ExportViaGnuplot(self, action):
        self.abort_selection()

        globals.app.plot_postscript(self.project, self.plot)
        




    #
    # TESTING
    #
    def on_action_PeakFinder(self, action):
        self.abort_selection()

        # we will simply take the first line available.
        layer = self.request_active_layer()
        line = layer.lines[0]

        print "USING LINE ", line

        p = globals.app.plugins['PeakFinder']
        data = line.source.get_data()

        print
        print "Peak Search:"
        peaks = p.find_peaks(data[line.cx], data[line.cy], 600, 5)
        for x, y in peaks:
            print "  %f : %f" % (x,y)
        print

        p = globals.app.plugins['PeakFinder::GTK::DialogBuilder']
        dialog = p.new_dialog()
        dialog.run()

        # a dialog should ask for the following:

        # Line (=> cx and cy will be automatically determined)
        # threshold
        # accuracy
        # max. nr. of points before aborting.

        # It should then have a list view with the list of points
        # and some options, e.g. 'add as label'.

        # In the next step, we will have a SIMS isotope library in
        # the SIMS plugin.  The SIMS plugin can then utilize the find_peak
        # method, look up the isotopes and determine the possible isotopes
        # from that!


#==============================================================================

# register only for pygtk < 2.8
if gtk.pygtk_version[1] < 8:
    gobject.type_register(MatplotlibWidget)        
        


