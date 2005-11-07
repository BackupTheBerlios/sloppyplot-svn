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


import logging
logger = logging.getLogger('Gtk.gnuplot_window')


import pygtk # TBR
pygtk.require('2.0') # TBR

import gtk, gobject

import re
import os.path

from Sloppy.Base import uwrap
from Sloppy.Base.objects import Axis
from Sloppy.Base import error
from Sloppy.Base.backend import BackendRegistry


from Sloppy.Lib.Undo import UndoInfo, UndoList, ulist

import gtkutils



class GnuplotWindow( gtk.Window ):

    def __init__(self, app, project, plot):
        gtk.Window.__init__(self)
        self.set_size_request(width=360,height=400)
        
        self.app = app
        self.project = project
        self.plot = None # will be set after everything else is set up
        self.backend = None
        self.cblist = []
        
        # some icons are not right at all....
        groups = {
            'Common':
            [('Replot', gtk.STOCK_REFRESH, 'Replot',
              '<control>R', 'Replot everything', '_cb_replot'),
             ('Edit', gtk.STOCK_PROPERTIES, 'Edit Plot',
              None, 'Edit Plot', '_cb_edit_plot'),
             ('ZoomSelection', gtk.STOCK_ZOOM_FIT, 'use current range',
              None, 'Use Current Range', '_cb_zoom_selection'),
             ('ZoomAutoscale', gtk.STOCK_ZOOM_100, 'do not limit range',
              None, 'Do not limit Range', '_cb_zoom_autoscale'),
             ('ExportPostscript', gtk.STOCK_SAVE, 'export as postscript',
              None, 'Export as Postscript file', '_cb_export_postscript')
             ]
            }
        
        ui = \
        """
        <ui>
          <toolbar name='Toolbar'>
            <toolitem action='Replot'/>            
            <separator/>
            <toolitem action='Edit'/>
            <toolitem action='ZoomSelection'/>
            <toolitem action='ZoomAutoscale'/>
            <separator/>
            <toolitem action='ExportPostscript'/>
          </toolbar>
        </ui>
        """
        
        self.uimanager = self._construct_uimanager(groups,ui)
        self.toolbar = self._construct_toolbar()

        # vbox 
        self.vbox = gtk.VBox(False)
        self.vbox.pack_start(self.toolbar, expand=False, fill=True)
        self.vbox.pack_start(self._construct_history(), expand=True, fill=True)
        self.vbox.show()
        self.add(self.vbox)

        self.connect("destroy", (lambda sender: self.destroy()))

        self.project.sig_connect("close", (lambda sender: self.destroy()))
        self.set_plot(plot)

    def set_plot(self, plot):

        for cb in self.cblist:
            cb.disconnect()
        self.cblist = []

        self.backend is not None and self.backend.disconnect()

        if id(plot) == self.plot:
            return

        # disconnect signals of old plot
        if self.plot is not None:
            cblist = self.plot.sig_cblist(receiver=self)
            print
            print "DISCONNECTING CALLBACKS"
            print cblist
            print
            self.plot.sig_disconnect(cblist)            

        self.plot = plot

        if plot is None:
            self.set_title("No plot")
            return
        else:        
            self.set_title( "Plot: %s" % plot.key )
        
        self.backend = project.new_backend('gnuplot/x11', plot=plot)

        # connect signals for treeview
        # these are disconnect by the backend if it closes

        self.cblist = [
            # backend signals
            self.backend.sig_connect('gnuplot-send-cmd', self.on_send_cmd),
            self.backend.sig_connect('gnuplot-finish-cmd', self.on_finish_cmd),

            # connect signal for plot
            plot.sig_connect('closed', (lambda sender: self.destroy())),
            plot.sig_connect('changed', (lambda sender: self.backend.draw()))
            ]

        self.backend.draw()


    def destroy(self, *args):
        logger.debug("Destroying gnuplot window.")
        self.set_plot(None)
        gtk.Window.destroy(self)
        

    # --- gui specific stuff -----------------------------------------------

    def _construct_history(self):
        # set up tree view
        model = gtk.TreeStore(str)
        #column = gtk.TreeViewColumn('gnuplot commands')
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('text', renderer)
        column.set_attributes(renderer, text=0)

        tv = gtk.TreeView()
        tv.set_model(model)
        tv.append_column(column)
        tv.get_selection().set_mode(gtk.SELECTION_SINGLE)
        tv.set_headers_visible(False)
        tv.show()

        # put treeview in a scrolled window
        sw = self.sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(tv)
        sw.show()

        self.treeview = tv
        self.model = model
        self.last_iter = None
        
        return sw

    
    def _construct_uimanager(self, actiongroups, ui, fix_actions = True):
        uimanager = gtk.UIManager()

        # construct action groups from dictionary 'actiongroups'
        self._actiongroups = {}
        for (group, group_actions) in actiongroups.iteritems():
            ag = gtk.ActionGroup(group)
            if fix_actions is True:
                group_actions = gtkutils.fix_actions(group_actions, self)
            ag.add_actions(group_actions)
            self._actiongroups[group] = ag

        # add action groups to ui manager
        uimanager = gtk.UIManager()
        for ag in self._actiongroups.values():
            uimanager.insert_action_group(ag, 0)

        # and build ui
        uimanager.add_ui_from_string(ui)

        self.add_accel_group(uimanager.get_accel_group())

        return uimanager


    def _construct_toolbar(self):        
        toolbar = self.uimanager.get_widget('/Toolbar')
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        toolbar.show()
        return toolbar


    # --- treeview callbacks -----------------------------------------------
    
    def on_start_plotting(self, sender):
        """
        When a gnuplot backend starts to plot, then the command
        history will be cleared.
        """
        self.model.clear()
    
    def on_send_cmd(self, sender, cmd):
        """
        When a gnuplot backend issues a command, it emits a signal
        'gnuplot-send-cmd'.  This callback appends the command
        to the treeview and remembers the corresponding iter as
        `self.last_iter`. It also scrolls down to this position.
        """
        self.last_iter = self.model.append( None, (cmd,) )
        self.treeview.scroll_to_cell(self.model.get_path(self.last_iter))
        
    def on_finish_cmd(self, sender, cmd, result):
        """
        When a gnuplot backend receives the result from a command,
        it emits a signal 'gnuplot-finish-cmd'.  This callback
        appends the result to the corresponding treeview item (using
        `self.last_iter` from 'on_send_cmd') _if_ there is a result.
        """
        if result is not None and len(result) > 0:
            self.model.append(self.last_iter, ("%s" % ("\n".join(result)),) )


    # --- action callbacks -------------------------------------------------

    def _cb_replot(self, action):
        self.backend.redraw()

    def _cb_edit_plot(self, action):
        self.app.edit_layer(self.plot)

    def _cb_zoom_selection(self, action):
        self.zoom_selection(undolist=self.project.undo)
        
    def _cb_zoom_autoscale(self, action):
        self.zoom_autoscale(undolist=self.project.undo)

    def _cb_export_postscript(self, action):

        self.app.plot_postscript(self.project, self.plot)

    # --- plot manipulation ------------------------------------------------

    def zoom_selection(self, undolist=[]):

        # TODO: We assume that there is a valid layer...
        layer = self.plot.layers[0]
        
        ul = UndoList()
        
        #
        # XRANGE
        #
        result = "\n".join(self.backend('show xrange'))
        regexp = re.compile('set xrange \[ (?P<xstart>.*) : (?P<xend>.*) \]')
        cv = regexp.search(result).groupdict()
        new_value = 'set xrange [ %(xstart)s : %(xend)s ]' % cv        

        xaxis = layer.xaxis
        xstart = cv['xstart']
        if xstart == '*':
            xstart = None
        xend = cv['xend']
        if xend == '*':
            xend = None
        uwrap.set( xaxis, 'start', xstart, undolist=ul )
        uwrap.set( xaxis, 'end', xend, undolist=ul )
        
        #
        # YRANGE
        #
        result = "\n".join(self.backend('show yrange'))
        regexp = re.compile('set yrange \[ (?P<ystart>.*) : (?P<yend>.*) \]')
        cv = regexp.search(result).groupdict()
        new_value = 'set yrange [ %(ystart)s : %(yend)s ]' % cv

        yaxis = layer.yaxis
        ystart = cv['ystart']
        if ystart == '*':
            ystart = None
        yend = cv['yend']
        if yend == '*':
            yend = None        
        uwrap.set(yaxis, 'start', ystart, undolist=ul)
        uwrap.set(yaxis, 'end', yend, undolist=ul)

        uwrap.emit_last( self.plot, "changed", undolist=ul )
        undolist.append(ul)



    def zoom_autoscale(self, undolist=[]):

        # TODO: We assume that there is a valid layer...
        layer = self.plot.layers[0]

        ul = UndoList()

        xaxis = layer.xaxis
        uwrap.set(xaxis,'start', None, undolist=ul)
        uwrap.set(xaxis,'end', None, undolist=ul)

        yaxis = layer.yaxis
        uwrap.set(yaxis,'start', None, undolist=ul)
        uwrap.set(yaxis,'end', None, undolist=ul)

        uwrap.emit_last( self.plot, "changed", undolist=ul )            
        undolist.append(ul)    




    
