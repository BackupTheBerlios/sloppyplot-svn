
from Sloppy.Lib.Undo import UndoList, ulist
from Sloppy.Base.dataset import Table
from Sloppy.Base import uwrap, pdict, globals
from Sloppy.Base.objects import *

import numpy

import logging
logger = logging.getLogger('Plugin.Core')


def create_plot_from_datasets(project, datasets, plot_label=None, undolist=None):
    """
    Creates a new plot from the list of given Datasets.

    >>> create_plot_from_datasets([ds1,ds2], 'my dataset')

    The method tries to guess, which lines to use as X/Y pairs,
    using the 'designation' given in the Dataset's tables.

    Returns the new plot or None if not dataset was given
    or if the Plot could not be constructed.
    """

    if undolist is None:
        undolist = project.journal

    ul = UndoList().describe("Create plot from datasets")

    if len(datasets) == 0:
        logger.error("No datasets given!")
        return

    if plot_label is None:
        plot_key = pdict.unique_key(project.plots, datasets[0].key)
        plot_label = plot_key

    lines = []
    for dataset in datasets:
        cx = None
        j = -1
        for name in dataset.names:
            info = dataset.infos[name]
            j += 1
            if cx is None:
                # skip if this is no X value
                if info.designation != 'X':
                    continue
                else:
                    cx = j
            else:
                # skip if this is no Y value
                if info.designation != 'Y':
                    continue
                else:
                    lines.append(Line(source=dataset, cx=cx, cy=j))
                    cx = None

    if len(lines) == 0:
        logger.error("The Dataset contains no X/Y column pair.")
        return

    layer = Layer(lines=lines)
    plot = Plot(title=plot_label, key=plot_key, layers=[layer])

    project.add_plots([plot], undolist=ul)
    undolist.append(ul)
    
    return plot




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
    ds = Table(a)
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

    ds2 = Table(a)
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


