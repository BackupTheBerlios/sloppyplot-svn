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


import os

from os.path import abspath,isfile,isdir,join, basename
from shutil import rmtree

from Sloppy.Lib.Undo import *
from Sloppy.Lib import Signals
from Sloppy.Lib.Props import *

from Sloppy.Base.objects import Plot, Axis, Line, Layer, new_lineplot2d
from Sloppy.Base.dataset import Dataset
from Sloppy.Base.backend import Backend, BackendRegistry
from Sloppy.Base.table import Table
from Sloppy.Base.dataio import ImporterRegistry, ExporterRegistry, importer_from_filename, Importer, ImportError
from Sloppy.Base.plugin import PluginRegistry
from Sloppy.Base import pdict, uwrap, const, utils

from Sloppy.Base.progress import SimpleProgressList


import logging
cli_logger = logging.getLogger('cli')
cli_logger.setLevel(logging.info)  # TODO: This should not be set here
logger = logging.getLogger('Base.project')




README="""
The file you are just looking at is part of a SloppyPlot archive.
SloppyPlot is a scientific plotting application that can be obtained
from 

  http://sloppyplot.berlios.de.

This archive contains of a project description 'project.xml' and the
corresponding datasets.  Each dataset is a single file in the
subdirectory 'datasets'.  If you need to get this data without
SloppyPlot, you can extract the file from this archive and read it
using any netCDF utility (e.g. 'ncdump'). For further information
about netCDF, see 

  http://my.unidata.ucar.edu/content/software/netcdf/index.html  
"""



class Project(Container):

    label = Prop(coerce=unicode)
    comment = Prop(coerce=unicode)

    plots = ListProp(types=Plot)
    datasets = ListProp(types=Dataset)

    backends = ListProp(types=Backend)
    
    
    def __init__(self,*args,**kwargs):
        Container.__init__(self, **kwargs)       
        self.journal = UndoRedo()
        self._archive = None
        self.app = None


    def close(self):
        " Close project properly. "
        
        for dataset in self.datasets:
            dataset.close()
        for plot in self.plots:
            plot.close()
        if self._archive is not None:
            self._archive.close()
        
        # disconnect all opened backends
        for backend in self.backends:
            backend.disconnect()
       
        Signals.emit(self, 'close')
        self.app = None # TODO: this should be unnecessary if the app catches the signal

    #----------------------------------------------------------------------        
    __filename = None
    def get_filename(self):
        return self.__filename
    def set_filename(self,value):
        self.__filename = abspath(value)
    filename = property(get_filename,set_filename)

    def get_directory(self):
        if self.filename is not None:
            return os.path.dirname(self.filename)
        else:
            return os.path.curdir

    #----------------------------------------------------------------------

    def get_dataset(self, key, default=-1):
        return pdict.xn_get(self.datasets, key, default=default)


    def get_plot(self, key, default=-1):
        return pdict.xn_get(self.plots, key, default=default)

    
    def has_dataset(self, key):
        return pdict.xn_has_key(self.datasets, key)


    def has_plot(self, key):
        return pdict.xn_has_key(self.plots, key)


    def add_datasets(self, datasets, undolist=None):
        if undolist is None:
            undolist = self.journal

        if len(datasets) == 0:
            undolist.append(NullUndo())
        
        ul = UndoList()
        ul.describe("Append Dataset to Project")

        for dataset in datasets:
            new_key = pdict.unique_key(self.datasets, dataset.key)
            if new_key != dataset.key:
                uwrap.set(dataset, 'key', new_key, undolist=ul)
            ulist.append( self.datasets, dataset, undolist=ul )

        uwrap.emit_last(self.datasets, "changed", undolist=ul)            
        undolist.append(ul)
        
        cli_logger.info("Added %d dataset(s)." % len(datasets) )
        
        
    def add_dataset(self, dataset, undolist=None):
        self.add_datasets([dataset], undolist=undolist)

    
    def add_plots(self, plots, undolist=None):
        if undolist is None:
            undolist = self.journal

        if len(plots) == 0:
            undolist.append(NullUndo())

        ul = UndoList()
        ul.describe("Append Plots to Project")

        for plot in plots:
            new_key = pdict.unique_key(self.plots, plot.key)
            if new_key != plot.key:
                uwrap.set(plot, 'key', new_key, undolist=ul)
            ulist.append(self.plots, plot, undolist=ul)

        uwrap.emit_last(self.plots, "changed", undolist=ul)
        undolist.append(ul)

        cli_logger.info("Added %d plot(s)." % len(plots) )
        

    def add_plot(self, plot, undolist=None):
        self.add_plots([plot], undolist=undolist)


    def remove_datasets(self, datasets, undolist=None):
        if undolist is None:
            undolist = self.journal

        removed_datasets = list()
        for dataset in datasets:
            try:
                dataset = self.get_dataset(dataset)                
                self.datasets.remove(dataset)
            except KeyError, msg:
                logger.error(msg)
            except ValueError, msg:
                logger.error(msg)
            else:
                removed_datasets.append(dataset)
                
        undolist.append( UndoInfo(self.add_datasets, removed_datasets).describe("Remove Dataset") )
        Signals.emit(self.datasets, "changed")


    def remove_dataset(self, dataset, undolist=None):
        self.remove_datasets([dataset], undolist=undolist)

        
    def remove_plots(self, plots, undolist=None):
        if undolist is None:
            undolist = self.journal

        removed_plots = list()
        for plot in plots:
            try:
                plot = self.get_plot(plot)                                
                self.plots.remove(plot)
                plot.close()
            except KeyError, msg:
                logger.error(msg)
            except ValueError, msg:
                logger.error(msg)
            else:
                removed_plots.append(plot)

        undolist.append( UndoInfo(self.add_plots, removed_plots).describe("Remove Plot") )
        Signals.emit(self.plots, "changed")


    def remove_plot(self, plot, undolist=None):
        self.remove_plots([plot], undolist=undolist)
        
        
    def rename_dataset(self, xn_dataset, new_key, undolist=None):
        """
        Rename a Dataset and make sure that its key is unique.
        The name might be modified so if the key is important to you,
        you might want to check it afterwards.
        Returns the Dataset.
        """
        if undolist is None:
            undolist = self.journal

        dataset = self.get_dataset(xn_dataset)

        dslist = [ds for ds in self.datasets]
        dslist.remove(dataset)
        new_key = pdict.unique_key(dslist, new_key)
        
        uwrap.set(dataset, 'key', new_key, undolist=undolist)
        return dataset


    def rename_plot(self, xn_plot, new_key, undolist=None):
        " Analogon to `rename_dataset`. "
        if undolist is None:
            undolist = self.journal

        plotlist = [plot for plot in self.plots]
        plot = self.get_plot(xn_plot)
        plotlist.remove(plot)
        new_key = pdict.unique_key(plotlist, new_key)
        
        uwrap.set(plot, 'key', new_key, undolist=undolist)
        return plot

    #----------------------------------------------------------------------

    def import_datasets(self, filenames, importer, progresslist=None, undolist=None):
        if undolist is None:
            undolist = self.journal

        if isinstance(importer, basestring):
            importer = ImporterRegistry.new_instance(importer)
        elif not isinstance(importer, Importer):
            raise TypeError("'importer' needs to be a key or a valid Importer instance.")

        # To ensure a proper undo, the Datasets are imported one by one
        # to a temporary dict.  When finished, they are added as a whole.
        new_datasets = list()

        progresslist = progresslist or self.app.progresslist
        pl = progresslist(filenames)
        for filename in pl:
            try:
                tbl = importer.read_table_from_file(filename)
            except ImportError, msg:
                pl.fail(msg)
                continue

            root, ext = os.path.splitext(basename(filename))
            filename = utils.encode_as_key(root)
            ds = Dataset(key=filename, data=tbl)
            ds.metadata['Import-Source'] = unicode(filename)
            ds.metadata['Import-Filter'] = unicode(importer.blurb)

            new_datasets.append(ds)
            pl.succeed()

        pl.finish()

        if len(new_datasets) > 0:
            ul = UndoList().describe("Import Dataset(s)")
            self.add_datasets(new_datasets, undolist=ul)
            undolist.append(ul)
        else:
            undolist.append(NullUndo())


    def create_plot_from_datasets(self, datasets, plot_label=None, undolist=None):
        """
        Creates a new plot from the list of given Datasets.
        
        >>> create_plot_from_datasets([ds1,ds2], 'my dataset')

        The method tries to guess, which lines to use as X/Y pairs,
        using the 'designation' given in the Dataset's tables.
        
        Returns the new plot.
        """
        if undolist is None:
            undolist = self.journal
        
        if len(datasets) == 0: return
        
        if plot_label is None:
	    plot_key = pdict.unique_key(self.plots, datasets[0].key)
            plot_label = plot_key

        lines = []
        for dataset in datasets:
            dataset = self.get_dataset(dataset)
            table = dataset.data
            if not isinstance(table, Table):
                raise TypeError("Dataset data is not a Table object.")

            cx = None
            j = -1
            for column in table.get_columns():
                j += 1
                if cx is None:
                    # skip if this is no X value
                    if column.designation != 'X':
                        continue
                    else:
                        cx = j
                else:
                    # skip if this is no Y value
                    if column.designation != 'Y':
                        continue
                    else:
                        lines.append( Line(source=dataset,
                                           cx=cx, cy=j) )
                        cx = None

        if len(lines) == 0:
            logger.error("The Dataset contains no X/Y column pair.")
            return
            
        layer = Layer(lines=lines)
        plot = Plot(title=plot_label, key=plot_key, layers=[layer])

        ui = UndoList().describe("Create Plot from Datasets")
        self.add_plots( [plot], undolist=ui )
        undolist.append(ui)   
        
        return plot


    def new_dataset(self, key='dataset', undolist=None):
        """
        Add a new Dataset object to the Project.

        The `data` field contains a nearly empty numarray (1 row, 2
        columns, all zero).

        If no key is given, then one is created.  If the key already
        exists, then the method assures that it is unique within the
        Project.

        Returns newly created Dataset.
        """
        if undolist is None:
            undolist = self.journal
        
        key = pdict.unique_key(self.datasets, key)
        ds = Dataset()
        pdict.setitem(self.datasets, key, ds)
        ds.data = Table(nrows=1,ncols=2)
        ds.data.column(0).designation = 'X'
        ds.data.column(1).designation = 'Y'        
        Signals.emit(self.datasets, "changed")

        ui = UndoInfo(self.remove_objects, [ds], False)
        ui.describe("Create new Dataset '%s'" % key)
        undolist.append(ui)
        
        return ds


    def add_datasets_to_plot(self, datasets, plot, undolist=None):
        """
        Adds the given Datasets to Dataset to the Plot object.
        
        >>> add_datasets_to_plot( [ds1,ds2], plot )

        Returns the Plot object.
        """
        if undolist is None:
            undolist = self.journal
        
        # make sure we are talking about an iterable object
        if not isinstance( datasets, (list,tuple) ):
            datasets = [datasets]

        ul = UndoList().describe("Add Datasets to Plot")

        try:
            layer = plot.layers[0]
        except KeyError:
            layer = Layer(type='lineplot2d')
            
        for dataset in datasets:
            dataset = self.get_dataset(dataset)
            line = Line(source=dataset, label = dataset.key)
            ulist.append( layer.lines, line, undolist=ul )

        uwrap.emit_last(self.plot, "plot-changed", undolist=ul)
        undolist.append( ul )
        
        return plot

        
        

    def new_plot(self, undolist=None):
        " Returns a new Plot. "
        if undolist is None:
            undolist = self.journal
        
        new_plot = new_lineplot2d()
        new_plot.key = pdict.unique_key(self.plots, "new lineplot2d")
        self.add_plot(new_plot)
        ui = UndoInfo(self.remove_plot, new_plot).describe("New Plot")
        undolist.append(ui)

        Signals.emit(self.plots, "changed")
        
        return new_plot    


    def remove_objects(self, objects, confirm=True, undolist=None):
        """
        Remove the given objects (datasets or plots) from the current
        Project. Returns nothing.
        """
        if undolist is None:
            undolist = self.journal

        # if you add an option confirm, make sure that it is False
        # when GtkApplication calls it.
        ul = UndoList().describe("Remove objects")
        
        datasets = list()
        plots = list()
        for obj in objects:                       
            if isinstance(obj, Dataset):
                datasets.append(obj)
            elif isinstance(obj, Plot):
                plots.append(obj)

        if len(datasets) > 0:
            self.remove_datasets(datasets, undolist=ul)
            
        if len(plots) > 0:
            self.remove_plots(plots, undolist=ul)
        
        undolist.append(ul)
        
        return None





    #----------------------------------------------------------------------
    def plot(self, plot=0, key=const.DEFAULT_BACKEND):
        plot = self.get_plot(plot)
        backend = self.request_backend(key, plot=plot)
        backend.draw()
        return backend

    def find_backends(self, key=None, plot=None):
        matches = self.backends
        if key is not None:
            klass = BackendRegistry.get_class(key)            
            matches = [item for item in matches if isinstance(item, klass)]
        if plot is not None:
            matches = [item for item in matches if repr(item.plot) == repr(plot)]
        return matches

    def request_backend(self, key, plot=None):
        print "Requesting Backend ", key, "for plot", plot
        
        matches = self.find_backends(key=key, plot=plot)
        print "===> matches = ", matches
        if len(matches) > 0:
            return matches[0]
        else:
            backend = BackendRegistry.new_instance(key, project=self, plot=plot)            
            self.backends.append(backend)
            return backend
        
    def remove_backend(self, backend):
        try:
            self.backends.remove(backend)
        except ValueError:
            logger.warn("remove_backend: Could not find Backend %s in Project." % backend)
            
    #----------------------------------------------------------------------
    def list_plots(self, verbose=True):
        rv = [ "Listing %d Plots:" % len(self.plots)]
        j = 0
        for plot in self.plots:
            rv.append("  %2d: %s" % (j, plot.key))
            j += 1

        result = "\n".join(rv)
        if verbose is True:
            print result            
        return result


    def list_datasets(self, verbose=True):
        rv = ["Listing %d Datasets:" % len(self.datasets)]
        j = 0
        for dataset in self.datasets:
            rv.append("  %2d: %s" % (j, dataset.key))
            j += 1

        result = "\n".join(rv)
        if verbose is True:
            print result
        return result


    def list_backends(self, verbose=True):       
        backends = BackendRegistry.find_instances(project=self)
            
        rv = ["Listing %d Backends:" % len(backends)]
        for backend in backends:
            rv.append("  %s" % str(backend))

        result = "\n".join(rv)
        if verbose is True:
            print result
        else:
            return result


    def list_journal(self, verbose=True):
        rv = ["Listing Undo Journal"]
        rv.append( self.journal.dump() )

        result = "\n".join(rv)
        if verbose is True:
            print result
        else:
            return result


    def list(self, verbose=True):
        rv = []
        rv.append(self.list_datasets(verbose=False))
        rv.append(self.list_plots(verbose=False))
        
        result = "\n".join(rv)
        if verbose is True:
            print result            
        else:
            return result


    def __str__(self):
        return self.list(verbose=False)


    #----------------------------------------------------------------------
    # Undo/Redo

    
    def undo(self):
        if self.journal.can_undo() is True:
            cli_logger.info("Undoing action %s" % self.journal.undo_text() )
            self.journal.undo()
        else:
            cli_logger.info("Nothing to undo.")

    def redo(self):
        if self.journal.can_redo() is True:
            cli_logger.info("Redoing action %s" % self.journal.redo_text() )
            self.journal.redo()
        else:
            cli_logger.info("Nothing to redo.")




