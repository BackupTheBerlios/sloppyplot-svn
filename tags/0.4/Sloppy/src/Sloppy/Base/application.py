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

from ConfigParser import SafeConfigParser, NoOptionError
import os

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

        self.plugins = dict()
        self.progresslist = ProgressList
        self.recent_files = list()

        # make sure config path exists and then open config file
        if os.path.exists(const.PATH_CONFIG) is False:
            try:
                os.mkdir(const.PATH_CONFIG)
            except IOError, msg:
                logging.error("Big Fat Warning: Could not create config path! Configuration will not be saved! Please check permissions for creating '%s'. (%s)" % (PATH_CONFIG, msg))
        
        self.config_parser = self.read_configuration_file(const.CONFIG_FILE)

        
        # init() is a good place for initialization of derived class
        self.init()
        
        # Set up the Project...
        self._project = None
	if isinstance(project, basestring):
	    try:
		self.load_project(project)
	    except IOError:
                logger.error("Failed to load project '%s'\nSetting up an empty project instead." % project)                
		self.set_project(Project())
        else:
            self.set_project(project)

        self.init_plugins()

    def quit(self):
        self.set_project(None, confirm=True)
        self.write_configuration_file(self.config_parser, const.CONFIG_FILE)
        
        
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
            self._project.close()
            
        self._project = project
        if project is not None:
            project.app = self
            def detach_project(project):
                if id(self._project) == id(project):
                    self._project.app = None
                    self._project = None
                    
            # TODO: connect_once would be nice.
            Signals.connect(project, 'close', detach_project)


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

    def save_project_as(self):
        raise RuntimeError("This method needs to be implemented.")


    def load_project(self, filename):
        # load new project and if it is sucessfully loaded,
        # detach the old project
        new_project = load_project(filename)
        if new_project:
            self.set_project(new_project)

            # Add filename to list of recent_files __unless__
            # it is identical with the most recent file.
            new_filename = os.path.abspath(filename)
            if len(self.recent_files) == 0 or \
                   self.recent_files[0] != new_filename:                               
                self.recent_files.insert(0, new_filename)
                if len(self.recent_files) > 10:
                    self.recent_files.pop(-1)
                Signals.emit(self, "update-recent-files")


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

    #----------------------------------------------------------------------
    # CONFIGURATION FILE


    def read_configuration_file(self, filename):
        # read file
        scp = SafeConfigParser()

        filename = os.path.expanduser(filename)
        if os.path.isfile(filename) is not True:
            logger.info("No configuration file '%s' found." % filename)
        else:
            logger.info("Reading configuration file '%s'." % filename)
            scp.read([filename])  # os.path.expanduser('~/.myapp.cfg'

        # read list of recently used files
        if scp.has_section('RecentFiles'):
            ruf = list()
            for n in range(9):
                try:
                    filename = scp.get('RecentFiles', 'file%d' % n)
                    if filename is not None:
                        ruf.append(filename)
                except NoOptionError:
                    pass

            print "RUF"
            print ruf

            self.recent_files = ruf

        return scp


    def write_configuration_file(self, scp, filename):
        logger.info("Writing configuration file '%s'." % filename)

        # create list of recently used files
        ruf = self.recent_files

        n = 1
        scp.remove_section('RecentFiles')
        scp.add_section('RecentFiles')
        for file in ruf:
            scp.set('RecentFiles', 'file%d' % n, file)
            n += 1

        # write file
        filename = os.path.expanduser(filename)
        fd = open(filename, 'w+')
        scp.write(fd)
        fd.close()


    #----------------------------------------------------------------------
    # MISC

    def clear_recent_files(self):
        self.recent_files = list()
        Signals.emit(self, 'update-recent-files')



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

