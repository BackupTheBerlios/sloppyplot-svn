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
logger = logging.getLogger('application')

import os, glob

import Sloppy

from Sloppy.Lib.Undo import *
from Sloppy.Lib.Signals import HasSignals
from Sloppy.Lib.ElementTree.ElementTree import Element, SubElement
from Sloppy.Lib.Check import values_as_dict

from Sloppy.Base.objects import Plot, Axis, Line, Layer, SPObject
from Sloppy.Base.dataset import Dataset
from Sloppy.Base.project import Project
from Sloppy.Base.projectio import load_project, save_project, ParseError
from Sloppy.Base import \
     uwrap, utils, iohelper, globals, config, error, dataio, version


#------------------------------------------------------------------------------
# Path Handling

import Sloppy
from os.path import join, sep, curdir, expandvars, expanduser

class PathHandler:
    def __init__(self):
	# TODO: determine from sys.prefix somehow
        internal_path = Sloppy.__path__[0]
        
        base_dir = internal_path
        system_prefix_dir = join(sep, 'usr')
        example_dir = join(sep,'usr','share','sloppyplot','examples')
        data_dir = join(example_dir, 'data')
        plugins = join(internal_path, 'Plugins')
        logfile = join(sep,'var','tmp','sloppy','sloppyplot.log')
        current_dir = curdir
        
        # determine config path
        if os.environ.has_key('XDG_CONFIG_HOME'):
            xdg_path = expandvars('${XDG_CONFIG_HOME}')
            cfg_path = join(xdg_path, 'sloppyplot')
        else:
            home_path = expanduser('~')
            cfg_path = join(home_path, '.config', 'sloppyplot')

        config_dir = cfg_path
        config = join(config_dir, 'config.xml')

        self.__dict__.update(locals())



#------------------------------------------------------------------------------        
class Application(SPObject):

    """
    The Application object manages all application-wide settings.
    There is exactly one instance of this object. During initialization,
    the Application object registers itself in globals.app, which
    every package can access.

    The Application is responsible for managing:
      - pathes (app.path)
      - plugins (app.plugins)
      - templates (not yet accessible through the app, see globals)
      - the current project

    Since many important functions are only available in the 'core'
    plugin, you can access it via application.core.

    Application also provides a few simple functions for user inter-
    action:
      - ask_yes_no
      - status_msg
      - progress
      
    These should be overwritten in classes derived from Application.
    """
    
    def __init__(self):
        SPObject.__init__(self)        
        globals.app = self
        self._project = None
        
        # init signals
        self.sig_register('write-config')

        # TODO:
        self.sig_register('update::project')
        
        # TODO: update::recent_files
        self.sig_register('update-recent-files')

        # init path handler
        self.path = PathHandler()       
        
        # init config file
        self.eConfig = config.read_configfile(self, self.path.config)
                   
        # init recent files
        self.recent_files = []
        self.read_recentfiles()
        self.sig_connect("write-config", self.write_config_recentfiles)

        # read in existing templates
        self.read_templates()
        self.sig_connect("write-config", self.write_config_templates)

        # init() is a good place for initialization of derived class
        self.plugins = {}
        self.load_plugins()
        self.init()        

        # After everything is initialized, we can set up the project.
        self.set_project(None)
        
        # welcome message
        self.status_msg("%s %s" % (version.NAME, version.VERSION))


    def quit(self):
        self.set_project(None, confirm=True)

	# inform all other objects to update the config file elements
        self.sig_emit("write-config", self.eConfig)
        config.write_configfile(self.eConfig, self.path.config)
        


    # Plugin Handling -------------------------------------------------------
    
    def load_plugins(self):
        """
        Init the plugins from the plugin directories.

        Each sub-directory with a file __init__.py is considered a
        plugin. Code inspired by the plugin code from the foopanel
        project.

        A plugin needs to define the string attributes 'name',
        'authors', 'blurb', 'version' and 'license'; otherwise it will
        not be recognized properly.        
        """
        

        logger.debug("Initializing plugins.")
        
        def init_plugin(pluginpath, plugin_name):            
            d = os.path.join(pluginpath, plugin_name)
            if (not os.path.isdir(d)) or (not "__init__.py" in os.listdir(d)):
                return
            
            exec("import Sloppy.Plugins.%s as plugin" % plugin_name ) in locals()

            for attr in ['name','authors','blurb','version','license']:
                if not hasattr(plugin, attr):
                    raise AttributeError("Plugin is lacking required attribute '%s'" % attr)
            self.plugins[plugin.name] = plugin
            logger.info("Plugin %s loaded." % item)

            # the core plugin is special and deserves a little shortcut
            # notation
            if plugin.name == 'core':
                self.core = plugin
                

        # Currently only the system location for plugins is scanned.
        # TODO: add place for user plugins
        for path in [self.path.plugins]:
            for item in os.listdir(path):
                try:
                    init_plugin(self.path.plugins, item)
                except Exception, msg:
                    logger.error("Failed to load Plugin %s: %s" % (item, msg))        

        # If self.core is still undefined, then the required core
        # plugin has not been found and we will raise an Error!
        if not hasattr(self, 'core'):
            raise SystemExit("Core plugin could not be found! Check your installation.")

    #----------------------------------------------------------------------
    # PROJECT HANDLING
    
    def set_project(self, project, confirm=True):
        """
        Set the current project to the given 'project' object.
        Returns the new current object.
        """
        has_changed = (id(self._project) != id(project))        
        if self._project is not None and has_changed:
            self._project.close()

        self._project = project
        if project is not None:
            project.app = self
            def detach_project(project):
                if id(self._project) == id(project):
                    self._project.app = None
                    self._project = None
                    
            # TODO: connect_once would be nice.
            project.sig_connect('close', detach_project)

        if has_changed is True:
            self.sig_emit('update::project', 'project', self._project)        

        return self._project


    # be careful when redefining get_project in derived classes -- it will
    # not work, because the property 'project' always refers to the method
    # in this class.
    def get_project(self):
        return self._project
    project = property(get_project)


    def new_project(self, confirm=True):
        """
        Create a fresh new Project.
        """
        self.set_project(Project())
        return self.project


    def save_project(self):
        """
        Save current project either under the current filename,
        or if no such name is set, call save_project_as.
        """
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
        """
        Load new project from the file with the given 'filename'
        and if it is sucessfully loaded, detach the old project.
        """
        try:
            new_project = load_project(filename)
        except IOError, msg:
            self.error_msg("Error when trying to open project %s:\n\n%s" %
                           (filename, msg))
            return
        
        if new_project:
            self.set_project(new_project)

            # Add filename to list of recent_files __unless__
            # it is identical with the most recent file.
            new_filename = os.path.abspath(filename)
            if len(self.recent_files) == 0 or \
                   self.recent_files[0] != new_filename:                               
                self.recent_files.insert(0, new_filename)
                if len(self.recent_files) > 9:
                    self.recent_files.pop(-1)
                self.sig_emit("update-recent-files")            


    def _check_project(self):
        if not self.project:
            raise RuntimeError("No Project available")
        else:
            return self.project


    # Recent Files --------------------------------------------------------

    def clear_recent_files(self):
        self.recent_files = list()
        self.sig_emit('update-recent-files')

    def read_recentfiles(self):
        ruf = []
        for eFile in self.eConfig.findall('RecentFiles/File'):
            ruf.append( eFile.text )
        self.recent_files = ruf

    def write_config_recentfiles(self, app, eConfig):    

        eRecentFiles = eConfig.find("RecentFiles")
        if eRecentFiles is None:
            eRecentFiles = SubElement(eConfig, "RecentFiles")
        else:
            eRecentFiles.clear()
        
        for file in self.recent_files:
            eFile = Element("File")
            eFile.text = unicode(file)
            eRecentFiles.append(eFile)


    # Templates -----------------------------------------------------------
    
    def read_templates(self):
        
        templates = {}
        for eTemplate in self.eConfig.findall('IOTemplates/ImportTemplate'):
            key = eTemplate.get('key')
            logger.debug("Reading Importer Template '%s'" % key)
            
            data = {}
            data['blurb'] = eTemplate.get('blurb')
            data['importer_key'] = eTemplate.get('importer_key')
            data['extensions'] = eTemplate.get('extensions')
            data['defaults'] = iohelper.read_dict(eTemplate, 'Defaults')

            def GET(key):
                if eTemplate.attrib.has_key(key):
                    data[key] = eTemplate.attrib.get(key)

            GET('skip_options')

            logger.debug("Data is %s" % data)
            templates[key] = dataio.IOTemplate(**data)

        globals.import_templates.update(templates)
            

    def write_config_templates(self, sender, eConfig):       
        eTemplates = eConfig.find('IOTemplates')
        if eTemplates is None:
            eTemplates = SubElement(eConfig, 'IOTemplates')
        else:
            eTemplates.clear()            
                
        for key, tpl in globals.import_templates.iteritems():
            if tpl.immutable is False:
                logger.debug("Writing template %s" % key)
                eTemplate = SubElement(eTemplates, 'ImportTemplate')               

                keylist=['blurb','importer_key','extensions','skip_options']
                attrs = values_as_dict(tpl, keylist, default=None)
                attrs['key'] = key
                iohelper.set_attributes(eTemplate, attrs)
                iohelper.write_dict(eTemplate, 'Defaults', tpl.defaults)                
                
                

    # Simple User I/O -----------------------------------------------------

    def ask_yes_no(self, msg):
        return True

    def error_msg(self, msg):
        print "error: %s" % msg
        
    def status_msg(self, msg):
        print msg

    def progress(self, fraction):
        " -1 = hide progress. fraction should be a float between 0 and 1"
        if progress == -1:
            return
        length=10
        full=int(float(fraction)*length)
        left=length-full
        print "%s%s" % ("#"*full, "-"*left)


