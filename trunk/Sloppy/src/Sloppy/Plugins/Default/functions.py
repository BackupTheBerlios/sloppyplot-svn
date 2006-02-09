
from Sloppy.Lib.Undo import UndoList, ulist
from Sloppy.Base.dataset import Dataset
from Sloppy.Base import uwrap, pdict, globals
from Sloppy.Base.objects import *

import numpy



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


