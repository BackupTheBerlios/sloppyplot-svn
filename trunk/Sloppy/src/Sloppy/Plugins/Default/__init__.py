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


from Sloppy.Base.plugin import PluginRegistry
from Sloppy.Lib.Undo import UndoList, ulist

from Sloppy.Gtk import plugin
from Sloppy.Base import uwrap, pdict
from Sloppy.Base.table import Table


from Sloppy.Base.dataio import ImporterRegistry
from Sloppy.Base.dataset import Dataset
from Sloppy.Base.objects import *
from os.path import basename

class Plugin:

    def __init__(self, app):
        self.app = app
        
    def test_call(self):
        print
        print "TestCall !", self.app
        print



    def toggle_logscale_y(self, plot, layer, undolist=None):
        project = self.app.project
        if undolist is None:
            undolist = project.journal
            
        ul = UndoList().describe("Toggle logarithmic scale")

        axis = layer.request_axis("y", undolist=ul)
        if axis.scale != 'log':
            uwrap.set(axis, scale='log', undolist=ul)
            start = uwrap.get(axis, 'start')
            if start is not None and start < 0:
                uwrap.set(axis, start=None, undolist=ul)
        else:
            uwrap.set(axis, scale='linear', undolist=ul)

        uwrap.emit_last( plot, "plot-changed", undolist=ul )
        undolist.append(ul)



    def quick_xps_import(self, filename, ranges, undolist=None):
        
        project = self.app.project
        if undolist is None:
            undolist = project.journal

        importer = ImporterRegistry.new_instance('XPS')
        table = importer.read_table_from_file(filename, ranges=ranges)

        ds = Dataset(key=basename(filename), data=table)
        ds.metadata['Import-Source'] = unicode(filename)
        ds.metadata['Import-Filter'] = unicode('XPS')

        ul = UndoList().describe("Quick import Dataset(s)")
        project.add_datasets([ds], undolist=ul)
        undolist.append(ul)



    def add_experimental_plot(self, project, undolist=None):

        if undolist is None:
            undolist = project.journal

        ul = UndoList().describe("Experimental Plot")

        ds = Dataset()
        ds.key = pdict.unique_key(project.datasets, "exp_ds")
        ds.data = Table(colcount=2, rowcount=5)
        ds.data[0] = [1,2,3,4,5]
        ds.data[1] = [1,4,9,16,25]

        ds2 = Dataset()
        ds2.key = pdict.unique_key(project.datasets, "exp_ds2")
        ds2.data = Table(colcount=2, rowcount=4)
        ds2.data[0] = [10,17,3,8]
        ds2.data[1] = [1,89,48,1]

        ulist.append( project.datasets, ds, undolist=ul )
        ulist.append( project.datasets, ds2, undolist=ul )                

        plot = Plot()
        plot.key = pdict.unique_key(project.plots, "exp_plot")
        layer1 = Layer(type="line2d",
                       lines=[Line(source=ds,cx=0,cy=1), Line(source=ds2)],
                       x=0.0, y=0.0, width=1.0, height=0.5)
        layer2 = Layer(type="line2d",
                       lines=[Line(source=ds2,cx=0,cy=1)],
                       x=0.0, y=0.5, width=1.0, height=0.5)
        plot.layers = [layer1, layer2]
#        plot.layers.arrange(rowcount=1, colcount=2)
        
        ulist.append( project.plots, plot, undolist=ul )

        uwrap.emit_last(project.datasets, "changed")
        undolist.append(ul)
        
        



PluginRegistry.register("Default", Plugin)
