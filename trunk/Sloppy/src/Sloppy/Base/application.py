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

from Sloppy.Base.objects import Plot, Axis, Line, Layer, new_lineplot2d
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
        example_dir = join(sep,'usr','share','sloppyplot','Examples')
        data_dir = join(example_dir, 'Data')
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
class Application(object, HasSignals):

    def __init__(self, project=None):
	" 'project' may be a Project object or a filename. "
        object.__init__(self)
        globals.app = self
        
        # init signals
        HasSignals.__init__(self)
        self.sig_register('write-config')
        self.sig_register('notify::project')
        self.sig_register('update-recent-files')

        # init path handler
        self.path = PathHandler()       

        # init config file
        self.eConfig = config.read_configfile(self, self.path.config)

        # set up plugins

        # each sub-directory with a file __init__.py is considered a
        # plugin. Code taken from foopanel project.

        def init_plugin(pluginpath, plugin_name):
            print "Trying to load Plugin ", plugin_name

            d = os.path.join(pluginpath, plugin_name)
            if not os.path.isdir(d):
                return False
            if not "__init__.py" in os.listdir(d):
                return False

            try:
                exec("import Sloppy.Plugins.%s as plugin" % plugin_name ) in locals()                
            except Exception, msg:
                logger.error("Failed to load Plugin %s: %s" % (plugin_name, msg))
            else:
                logger.info("Plugin %s loaded." % plugin_name)
                globals.plugins[plugin.name] = plugin
            

        # TODO: load all plugins from a Directory
        init_plugin(self.path.plugins, 'Default')
        init_plugin(self.path.plugins, 'Sims')
        
        # init recent files
        self.recent_files = list()
        self.read_recentfiles()
        self.sig_connect("write-config",
                         (lambda sender: self.write_recentfiles()))

        # read in existing templates
        self.read_templates()
        self.sig_connect("write-config",
                         (lambda sender: self.write_templates()))

        # init() is a good place for initialization of derived class
        self.init()
        
        # Set up the Project...
        self._project = None
	if isinstance(project, basestring):
	    try:
		self.load_project(project)
	    except IOError, msg:
                logger.error("Failed to load project '%s'\nReason was:\n%s\nSetting up an empty project instead." % (project, msg))
		self.set_project(Project())
        else:
            self.set_project(project)

        # useful for gtk.Application
        self.init_plugins()
        
        # welcome message
        self.status_msg("%s %s" % (version.NAME, version.VERSION))



    def quit(self):
        self.set_project(None, confirm=True)

	# inform all other objects to update the config file elements
        self.sig_emit("write-config")
        config.write_configfile(self.eConfig, self.path.config)
        
        
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
            self.sig_emit('notify::project', self._project)        


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
                if len(self.recent_files) > 10:
                    self.recent_files.pop(-1)
                self.sig_emit("update-recent-files")            

    #----------------------------------------------------------------------
    # MISC

    def clear_recent_files(self):
        self.recent_files = list()
        self.sig_emit('update-recent-files')

    def read_recentfiles(self):
        ruf = []
        for eFile in self.eConfig.findall('RecentFiles/File'):
            ruf.append( eFile.text )
        self.recent_files = ruf

    def write_recentfiles(self):    

        eRecentFiles = self.eConfig.find("RecentFiles")
        if eRecentFiles is None:
            eRecentFiles = SubElement(self.eConfig, "RecentFiles")
        else:
            eRecentFiles.clear()
        
        for file in self.recent_files:
            eFile = Element("File")
            eFile.text = unicode(file)
            eRecentFiles.append(eFile)


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
            

    def write_templates(self):
        logger.debug("Writing templates.")
        
        eTemplates = self.eConfig.find('IOTemplates')
        if eTemplates is None:
            eTemplates = SubElement(self.eConfig, 'IOTemplates')
        else:
            eTemplates.clear()            
                
        for key, tpl in globals.import_templates.iteritems():
            if tpl.is_internal is False:
                logger.debug("Writing template %s" % key)
                eTemplate = SubElement(eTemplates, 'ImportTemplate')               

                attrs = tpl.get_values(['blurb','importer_key','extensions','skip_options'], default=None)
                attrs['key'] = key
                iohelper.set_attributes(eTemplate, attrs)
                iohelper.write_dict(eTemplate, 'Defaults', tpl.defaults)                
                
                

    def init_plugins(self):
        pass

    

    #----------------------------------------------------------------------
    # Simple user I/O
    #

    def ask_yes_no(self, msg):
        return True

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


    #------------------------------------------------------------------------------
    def import_datasets(self, project, filenames, template, undolist=None):

        if undolist is None:
            undolist = project.journal

        if isinstance(template, basestring): # template key
            template = globals.import_templates[template]

        # To ensure a proper undo, the Datasets are imported one by one
        # to a temporary dict.  When finished, they are added as a whole.
        new_datasets = list()

        n = 0.0
        N = len(filenames)
        self.progress(0)        
        for filename in filenames:
            self.status_msg("Importing %s" % filename)                       
            try:
                importer = template.new_instance()                
                ds = importer.read_dataset_from_file(filename)
            except dataio.ImportError, msg:
                self.error_msg(msg)
                continue
            except error.UserCancel:
                self.error_msg("Import aborted by user")
                continue

            root, ext = os.path.splitext(os.path.basename(filename))
            ds.key = utils.encode_as_key(root)

            new_datasets.append(ds)
            n+=1
            self.progress(n/N)

        self.progress(100)

        if len(new_datasets) > 0:
            ul = UndoList()
            if len(new_datasets) == 1:
                ul.describe("Import Dataset")
            else:
                ul.describe("Import %d Datasets" % len(new_datasets) )
                
            project.add_datasets(new_datasets, undolist=ul)
            undolist.append(ul)
            #msg = "Import of %d datasets finished." % len(new_datasets)
        else:
            undolist.append(NullUndo())
            #msg = "Nothing imported."

        self.progress(-1)
        #self.status_message(msg)
