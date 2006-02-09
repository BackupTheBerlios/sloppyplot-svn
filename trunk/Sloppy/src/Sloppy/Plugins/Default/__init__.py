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
Commonly used functions.
"""

from Sloppy.Lib.Undo import UndoList, ulist

from Sloppy.Gtk import plugin
from Sloppy.Base import uwrap, pdict, globals, dataio

from Sloppy.Base.dataset import Dataset
from Sloppy.Base.objects import *

import numpy, os.path


name = "Default"


def test_call():
    print
    print "TestCall ! Our app object is ", globals.app
    print



def toggle_logscale_y(plot, layer, undolist=None):
    project = globals.app.project
    if undolist is None:
        undolist = project.journal

    ul = UndoList().describe("Toggle logarithmic scale")

    updateinfo = {}
    axis = layer.yaxis
    if axis.scale != 'log':
        uwrap.set(axis, scale='log', undolist=ul)
        updateinfo['scale'] = 'log'

        start = axis.start
        if start is not None and start < 0:
            uwrap.set(axis, start=None, undolist=ul)
            updateinfo['start'] = None
    else:
        uwrap.set(axis, scale='linear', undolist=ul)

    # TODO: replace by something like
    #uwrap.emit_last(layer, "notify::axes", updateinfo=updateinfo, undolist=ul)
    uwrap.emit_last( plot, "changed", undolist=ul )
    undolist.append(ul)


def add_experimental_plot(project, undolist=None):

    if undolist is None:
        undolist = project.journal

    ul = UndoList().describe("Experimental Plot")

    a = numpy.array(
        [(1,1),
         (2,4),
         (3,9),
         (4,16),
         (5,25)],
         dtype = {'names':['col1','col2'],
                  'formats':['f4','f4']}
         )
    ds = Dataset(a)
    ds.infos['col2'].designation = 'Y'
    ds.key = pdict.unique_key(project.datasets, "exp_ds")


    a = numpy.array(
        [(10,12),
         (11,14),
         (13,-5),
         (16,8),
         (18,0)],
         dtype = {'names':['col3','col4'],
                  'formats':['f4','f4']}
         )

    ds2 = Dataset(a)
    ds2.infos['col4'].designation = 'Y'        
    ds2.key = pdict.unique_key(project.datasets, "exp_ds2")

    plot = Plot()
    plot.key = pdict.unique_key(project.plots, "exp_plot")
    layer1 = Layer(type="line2d",
                   lines=[Line(source=ds,cx=0,cy=1),
                          Line(source=ds2,cx=0,cy=1)],
                   x=0.0, y=0.0, width=1.0, height=0.5)
    layer2 = Layer(type="line2d",
                   lines=[Line(source=ds2,cx=0,cy=1)],
                   x=0.0, y=0.5, width=1.0, height=0.5)
    plot.layers = [layer1, layer2]

    project.add_datasets([ds,ds2], undolist=ul)
    project.add_plot(plot, undolist=ul)
    undolist.append(ul)
