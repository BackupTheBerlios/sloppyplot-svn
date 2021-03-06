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
See documentation of the Plotter class for details.
"""

import logging, os

from Sloppy.Lib import Signals

from Sloppy.Base import uwrap, klassregistry

#==============================================================================
class Backend:
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

      connect -- open the connection to the backend
      disconnect -- close it again
      check_connection -- connect, if necessary

      clear -- clear the plotting output
      draw -- plot the data of self.plot
      redraw
      
    You might want to redefine the following:
    
      cd -- change the internal directory of the Backend
      pwd -- return the internal directory of the Backend

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

        self.set(project,plot)
        

    def set(self, project,plot):
        logging.debug("Assigning project %s to Plotter" % repr(project))

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
        # TODO: only redraw if we have already drawn something!
        self.redraw()
        
    def cb_project_closed(self, sender):
        logging.debug("The project '%s' is closing. The Plotter will close as well." % uwrap.get(sender, 'label'))
        if self.connected is True:
            self.disconnect()

    def get_description(self):
        """ Return a string describing the backend. """
        return self.options.get('description','unknown')
    description = property(get_description)


    #----------------------------------------------------------------------
    # methods that a Plotter might want to re-implement

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



# deprecated
Plotter = Backend

BackendRegistry = klassregistry.Registry("Backends")
