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
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger('application')

cli_logger = logging.getLogger('cli')
cli_logger.setLevel(logging.info)


from Sloppy.Lib.Undo import *
from Sloppy.Lib import Signals

from Sloppy.Base.objects import Plot, Axis, Line, Layer, new_lineplot2d
from Sloppy.Base.dataset import Dataset
from Sloppy.Base.project import Project
from Sloppy.Base.projectio import load_project, save_project, ParseError
from Sloppy.Base.backend import BackendRegistry
from Sloppy.Base.table import Table
from Sloppy.Base.dataio import ImporterRegistry, ExporterRegistry, importer_from_filename
from Sloppy.Base import uwrap, const

from Sloppy import Plugins
from Sloppy.Base.plugin import PluginRegistry


from Sloppy.Base.progress import ProgressList


class Application(object):

    def __init__(self, project=None):
	" 'project' may be a Project object or a filename. "

        # Set up the Project...
        self._project = None
	if isinstance(project, basestring):
	    try:
		project = load_project(project)
	    except IOError:
                error_msg("Failed to load project '%s'\nSetting up an empty project instead." % project)                
		project = Project()
	self.set_project(project)

        self.plugins = dict()
        self.init_plugins()
        self.progresslist = ProgressList
        
        self.journal = UndoRedo()


    #----------------------------------------------------------------------
    # INTERNAL

    def _check_project(self):
        if not self.project:
            raise RuntimeError("No Project available")
        else:
            return self.project
        

    #----------------------------------------------------------------------
    # PROJECT HANDLING
    
    def set_project(self, project, confirm=True):

        # if project changes, then close the Project properly!
        if self._project is not None and id(project) != id(self._project):
            print "Closing Project"
       
            for dataset in self.project.datasets:
                dataset.close()
            for plot in self.project.plots:
                plot.close()
            if self.project._archive is not None:
                self.project._archive.close()

            self.project.app = None
        
            # disconnect all opened backends
            for backend in self.project.backends:
                backend.disconnect()
       
            Signals.emit(self.project, 'close')

            self._project = None
        

        self._project = project
        if project is not None:
            project.app = self


    # be careful when redefining get_project in derived classes -- it will
    # not work, because the property 'project' always refers to the method
    # in this class.
    def get_project(self):
        return self._project
    project = property(get_project)


    def new_project(self, confirm=True):
        self.set_project(Project())
        return self.project
    

    # TODO: Hmmm. Maybe still put this into project.py ?
    def close_project(self, confirm=True):
        pj = self._check_project()
        self.set_project(None)


    def save_project(self):
        if self.project is None:
            return None
        
        if self.project.filename is not None:
            save_project(self.project)
            self.project.journal.clear()
        else:
            self.save_project_as()


    def load_project(self, filename):
        # load new project and if it is sucessfully loaded,
        # detach the old project
        new_project = load_project(filename)
        if new_project:
            # TODO: remove old plotter objects for this project
            # TODO: is the project deleted ?
            self.set_project(new_project)


    #----------------------------------------------------------------------
    # PLUGIN HANDLING
    
    def init_plugins(self):
        for key in PluginRegistry.iterkeys():
            self.plugins[key] = PluginRegistry.new_instance(key, app=self)

    def get_plugin(self, key):
        try:
            return self.plugins[key]
        except KeyError:
            raise RuntimeError("Requested plugin '%s' is not available." % key)


#------------------------------------------------------------------------------

import Numeric

def test_application():
    app = Application()
    p = app.new_project()
    

    # set up sample project
    print "Setting up sample project with a Dataset and a Plot."

    ds = p.new_dataset()

    data = ds.get_data()
    data.extend(20)
    data[0] = Numeric.arange(21)
    data[1] = Numeric.sin(data[0])

    layer = Layer(type='line2d',
                  lines=[Line(source=ds)],
                  axes = {'x': Axis(label="A Number (arb. units)"),
                          'y': Axis(label="The Sin (arb. units)")})

    plot = Plot(label=u"A silly example", layers=[layer], key="a plot")

    p.add_plot(plot)

    p.list()

    return app

