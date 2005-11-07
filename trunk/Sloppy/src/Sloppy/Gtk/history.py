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
logger = logging.getLogger('Gtk.history')

import gtk


# TODO

# [ ] automatically scroll to the end when receiving another command
#     (don't move marker though!)
# [ ] allow movement to previous/next error message
# [ ] give summary, how many messages are there (in between the previous/next
#     buttons



        
class GnuplotHistory( gtk.Alignment):

    COLUMN_TEXT = 0
    
    def __init__(self, backend):
        gtk.Alignment.__init__(self,0,0,1,1)

        # layout:

        # +-------------------+
        # | toolbar           |
        # +-------------------+
        # | treeview for      |
        # | messages          |
        # |                   |
        # |                   |
        # +-------------------+
        
        # set up tree view
        self.model = gtk.TreeStore(str)
        #column = gtk.TreeViewColumn('gnuplot commands')
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('text', renderer)
        column.set_attributes(renderer, text=self.COLUMN_TEXT)

        tv = self.treeview = gtk.TreeView()
        tv.set_model(self.model)
        tv.append_column(column)
        tv.get_selection().set_mode(gtk.SELECTION_SINGLE)
        tv.set_headers_visible(False)
        tv.show()

        # put treeview in a scrolled window
        sw = self.sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(tv)
        sw.show()



#         # construct toolbar
#         uimanager = gtk.UIManager()
#         ag = gtk.ActionGroup('Toolbar')
#         ag.add_actions(\
#             [
#             ('Previous',gtk.STOCK_MEDIA_PREVIOUS,
#              'Previous Message', '<control>P',
#              'Go to previous message', self.cb_previous),
#             ('Next', gtk.STOCK_MEDIA_NEXT,
#              'Next Message', '<control>N',
#              'Go to next message', self.cb_next),
#             ('Clear', gtk.STOCK_DELETE,
#              'Clear Message List', None,
#              'Clear Message List', self.cb_clear),
#             ('Hide', gtk.STOCK_CANCEL,
#              'Hide Window', None,
#              'Hide Window', self.cb_hide)
#             ])
#         uimanager.insert_action_group(ag,0)
#         #self.add_accel_group(uimanager.get_accel_group())

#         uimanager.add_ui_from_string(\
#         """
#         <ui>
#         <toolbar name='Toolbar'>
#           <toolitem action='Previous'/>
#           <toolitem action='Next'/>
#           <separator/>
#           <toolitem action='Clear'/>
#           <separator/>
#           <toolitem action='Hide'/>
#         </toolbar>
#         </ui>
#         """)
        
#         # construct toolbar
#         toolbar = uimanager.get_widget('/Toolbar')
#         toolbar.show()
        
        
        # put everything in one vbox
        vbox = gtk.VBox(False)
#        vbox.pack_start(toolbar, expand=False, fill=True)
        vbox.pack_start(sw, expand=True, fill=True)
        vbox.show()
        self.add(vbox)

        self._signals = []
        self._backend = None
        self.set_backend(backend)

        self.last_iter = None
        self.tv = tv


        # TODO: the backend is not set, but the plot is!
        # TODO: The history window is responsible for choosing the backend!
        
#     def set_backend(self, backend):
#         # remove obsolete signals
#         for signal in self._signals:
#             Signals.disconnect(signal)
# 	    self._signals.remove(signal)

#         self._backend = backend
#         if self.backend is None:
#             self.sw.set_sensitive(False)
#         else:
#             self.sw.set_sensitive(True)
#             self._signals.append( Signals.connect(
#                 backend, 'gnuplot-send-cmd', self.on_send_cmd))
#             self._signals.append( Signals.connect(
#                 backend, 'gnuplot-finish-cmd', self.on_finish_cmd))
#             self._signals.append( Signals.connect(
#                 backend, 'gnuplot-start-plotting', self.on_start_plotting))

#     def get_backend(self):
#         return self._backend

#     backend = property(get_backend, set_backend)


    
#     def on_delete(self,widget,*args):
#         """
#         Closing the history window will not delete it but only hide it.
#         """
#         self.hide()
#         return True


    def on_start_plotting(self, sender):
        """
        When a gnuplot backend starts to plot, then the command
        history will be cleared (unless requested otherwise).
        """
        # TODO: option to allow _not_ to clear the list
        self.model.clear()
    
    def on_send_cmd(self, sender, cmd):
        """
        When a gnuplot backend issues a command, it emits a signal
        'gnuplot-send-cmd'.  This callback appends the command
        to the treeview and remembers the corresponding iter as
        `self.last_iter`. It also scrolls down to this position.
        """
        self.last_iter = self.model.append( None, (cmd,) )
        self.tv.scroll_to_cell(self.model.get_path(self.last_iter))
        
    def on_finish_cmd(self, sender, cmd, result):
        """
        When a gnuplot backend receives the result from a command,
        it emits a signal 'gnuplot-finish-cmd'.  This callback
        appends the result to the corresponding treeview item (using
        `self.last_iter` from 'on_send_cmd') _if_ there is a result.
        """
        if result is not None and len(result) > 0:
            self.model.append(self.last_iter, ("%s" % ("\n".join(result)),) )


    def cb_previous(self, widget):
        logger.debug("Going to previous message.")
    def cb_next(self, widget):
        logger.debug("Going to next message.")
    def cb_clear(self, widget):
        logger.debug("Clearing message.")
        self.backend.history = []
        self.model.clear()
    def cb_hide(self, widget):
        self.hide()
        

    
