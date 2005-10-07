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
Generic plotting backend.
See documentation of the Backend class for details.
"""

import logging, os

from Sloppy.Lib import Signals

from Sloppy.Base import uwrap
from Sloppy.Base.table import Table


#------------------------------------------------------------------------------
# Backend Error
#

class BackendError(Exception):
    pass


#------------------------------------------------------------------------------
# Backend
#

class Backend(object):
    """
    'Backend' is the abstract base class for any plotting backend.
    Any actual implementation should use this as a base class.
    
    Each Backend holds two references to objects that determine, what
    the Backend should plot: `self.project` and `self.plot`.  Note
    that the project and the plot do not necessarily need to match! If
    during plotting any additional information is requested, then
    self.project is used as a data source. An actual case, where
    project and plot do not match might be the creation of a temporary
    plot referring to a project, e.g.  for a preview window.  This way
    you do not have to actually add the temporary plot to the project,
    but still let it refer to it.
    
    A third attribute is `self.options`, which holds any keyword
    arguments passed to the Backend during initialization as well as
    any options defined as standard options in the
    BackendRegistry. The first will override the latter.
    
    Any real implementation must implement the following:

        - connect -- open the connection to the backend
        - disconnect -- close it again
        - check_connection -- connect, if necessary

        - clear -- clear the plotting output
        - draw -- plot the data of self.plot
        - redraw
      
    You might want to redefine the following:
    
        - cd -- change the internal directory of the Backend
        - pwd -- return the internal directory of the Backend

    For information on how to register a new Backend, consult the
    BackendRegistry documentation and have a look at the sample
    Backend implementations.    
    """

    def __init__(self,project=None,plot=None,extrakw=None,**kw):

        """
        Initalization consists of:

            - save keyword arguments as self.options
            - merge in any extra keywords assigned via BackendRegistry.register
            - assign `self.project` and `self.plot`
            - call self.connect()

        Do not overwrite this method, use self.init() for custom
        initialization!
        """
        # set options and merge keywords from BackendRegistry.register
        self.options = dict(kw)
        if extrakw:
            self.options.update(extrakw)
                  
        # call functions for custom initialization
        self.init() # custom initialization
        self.connect()
        
        self.project = None
        self.plot = None
        self.Signals = {}

        self._layer = None
        
        self.set(project,plot)
        

    def set(self, project,plot):
        logging.debug("Assigning project %s to Backend" % repr(project))

        # if necessary, detach messages from old project
        for signal in self.Signals:
            Signals.disconnect(signal)
        self.Signals.clear()
            
        # assign project and plot
        self.plot = plot
        self.project = project
        if self.project is not None:
            logging.debug("Connecting Signals.")
            self.Signals['close'] = Signals.connect(
                self.project, 'close', self.cb_project_closed)
            self.Signals['plot-changed'] = Signals.connect(
                self.plot, 'plot-changed', self.cb_plot_changed)
            self.Signals['plot-closed'] = Signals.connect(
                self.plot, 'closed', (lambda sender: self.disconnect()))

    def cb_plot_changed(self, sender):
        """
        @todo: only redraw if we have already drawn something!
        """
        self.redraw()
        
    def cb_project_closed(self, sender):
        logging.debug("The project '%s' is closing. The Backend will close as well." % uwrap.get(sender, 'label'))
        if self.connected is True:
            self.disconnect()

    def get_description(self):
        """ Return a string describing the backend. """
        return self.options.get('description','unknown')
    description = property(get_description)


    #----------------------------------------------------------------------
    # Methods that a Backend might want to re-implement
    #

    def connect(self):
        """ Open the connection to the backend. """
        self.connected = True

    def disconnect(self):
        """ Close the connection to the backend. """
        if self.project is not None:
            self.project.remove_backend(self)
        self.set(None,None)        
        self.connected = False
        Signals.emit(self, 'backend-closed')
        Signals.disconnect(sender=self)
        Signals.disconnect(receiver=self)
    
    def check_connection(self):
        """ Connect (only) if necessary. """
        if not self.connected:
            self.connect()

    def clear(self):
        """ Clear the plot so that standard specific setting can be
        assumed."""
        pass

    def draw(self):
        """ Send plotting commands to the plot."""
        pass

    def redraw(self):
        pass


    #----------------------------------------------------------------------
    # Common Backend Utility Functions
    #

    def get_line_source(self, line):
        #:line.source            
        if line.source is None:
            raise BackendError("No Dataset specified for Line!")
        else:
            return line.source

    def get_table(self, source):
        if source.is_empty() is True:
            raise BackendError("No data for Line!")

        table = source.get_data()
        if not isinstance(table, Table):
            raise BackendError("Gnuplot Backend currently only supports data of type Table, while this is of %s" % type(table))
        return table

    def get_column_indices(self, line):
        #:line.cx
        if line.cx is None or line.cy is None:
            raise BackendError("No x or y source given for Line. Line skipped.")
        else:
            return line.cx, line.cy

    def get_line_label(self, line, table=None, cy=None):
        #:line.label:OK
        label = line.label
        if label is None:
            if table is not None and cy is not None:
                column = table.column(cy)
                label = column.label or column.key or uwrap.get(line, 'label')
            else:
                label = uwrap.get(line, 'label')
        return label


    def get_table_data(self, table, cx, cy):
        #:line.cx
        try:
            xdata = table[cx]
        except IndexError:
            raise BackendError("X-Index out of range (%s). Line skipped." % cx)


        #:line.cy
        try:
            ydata = table[cy]
        except IndexError:
            raise BackendError("Y-Index out of range (%s). Line skipped." % cy)

        return xdata, ydata


    #----------------------------------------------------------------------
    # Current Layer

    def get_layer(self):
        """
        Returns the current layer.
        Make sure that the current_layer actually exists.
        If this is not the case, the current_layer attribute is reset.
        """
        if self._layer is None or self.plot is None:
            return None
        if self._layer in self.plot.layers:
            return self._layer

        self.set_layer(None)
        return None

    def set_layer(self, layer):
        """
        Set the current layer.
        The layer must be either None or a Layer instance that is
        contained in self.layers.
        """
        if layer is None or layer in self.plot.layers:
            self._layer = layer
            # TODO: only when it changes!
            Signals.emit(self, "notify::current_layer", layer)
        else:
            raise ValueError("Layer %s can't be set as current, because it is not part of the Plot!" % layer)

    layer = property(get_layer, set_layer)            


#------------------------------------------------------------------------------
# BackendRegistry
#

BackendRegistry = {}
