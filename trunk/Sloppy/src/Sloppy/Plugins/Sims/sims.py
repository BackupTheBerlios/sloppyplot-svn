
from Sloppy.Base import pdict, uwrap, globals
from Sloppy.Base.objects import Plot, Line, Axis, Layer, Legend
from Sloppy.Base.dataset import Dataset
from Sloppy.Lib.Undo import UndoList, ulist

#------------------------------------------------------------------------------

def create_pfc(dataset, undolist=None):
    """
    Create new Plot from given Dataset, treating the Dataset as a PFC
    dataset, i.e.

    column 0 = time for Element 1
    column 1 = intensity for Element 1
    column 2 = time for Element 2
    column 3 = intensity for Element 2
    ...

    Returns the new Plot.
    """
    project = globals.app.project
    if undolist is None:
        undolist = project.journal

    table = dataset
    if table is None:
        logger.info("No dataset selected.")
        return

    if table.ncols % 2 == 1:
        logger.error("action_plot_profile_plot: Dataset '%s' has wrong shape." % dataset.key)
        return None

    lines = []
    for i in range(int(table.ncols/2.0)):
        l = Line( source=dataset, cx=i*2, cy=i*2+1 )
        lines.append(l)

    p = Plot( key = pdict.unique_key(project.plots, "profile_%s" % dataset.key),
              layers = [Layer(type='line2d',
                              lines=lines,
                              yaxis = Axis(scale="log",
                                           label='log SIMS intensity (cts/sec)',
                                           start=10,
                                           format='%L'),
                              xaxis = Axis(scale="linear",
                                           label='time (sec)'), 
                              title=u"SIMS depth profile of %s" % dataset.key,
                              legend = Legend(border=True,
                                              position='outside')                                  
                              )
                        ]

              )

    project.add_plot(p, undolist=undolist)



def create_spc(dataset, undolist=None):
    """
    Create new Plot from given Dataset, treating the Dataset as a SPC
    dataset. Returns the new Plot.
    """
    project = globals.app.project
    if undolist is None:
        undolist = project.journal

    table = dataset
    
    p = Plot( key = pdict.unique_key(project.plots, "spectrum_%s" % dataset.key),
              layers = [Layer(type='line2d',
                              lines=[Line( label=dataset.key,
                                           source=dataset,
                                           cx=0,
                                           cy=1 )
                                     ],
                              yaxis = Axis(scale="log",
                                           label='SIMS intensity (cts/sec)',
                                           start=10,
                                           format='%2.1e'),
                              xaxis = Axis(scale="linear",
                                           label='mass (amu)'),
                              title=u"SIMS mass spectrum of %s" % dataset.key,
                              )
                        ]

              )

    project.add_plot(p, undolist=undolist)
