

from Sloppy.Base import pdict, uwrap, globals
from Sloppy.Base.objects import Plot, Line, Axis, Layer, Legend
from Sloppy.Base.dataset import Dataset
from Sloppy.Gtk import plugin
from Sloppy.Lib.Undo import UndoList, ulist

import logging
logger = logging.getLogger('plugin.sims')


#------------------------------------------------------------------------------

def gtk_init(app):
    
    a = plugin.ActionWrapper('CreatePFC', "Create a SIMS profile from Dataset")
    a.connect(_cb_create_pfc)

    b = plugin.ActionWrapper('CreateSPC', 'Create a SIMS spectrum from Dataset')
    b.connect(_cb_create_spc)

    app.register_actions([a,b])


#----------------------------------------------------------------------

def _cb_create_pfc(action):
    dslist = globals.app.window.treeview.get_selected_datasets()
    project = globals.app.project

    ul = UndoList().describe("Create Profiles (PFC)")
    for ds in dslist:
        create_pfc(ds, undolist=ul)
    project.journal.append(ul)


def _cb_create_spc(action):
    dslist = globals.app.window.treeview.get_selected_datasets()
    project = globals.app.project

    ul = UndoList().describe("Create Spectra (SPC)")
    for ds in dslist:
        self.create_spc(ds, undolist=ul)
    project.journal.append(ul)


#----------------------------------------------------------------------

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

    table = dataset.get_data()   # TODO: check for Table
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

    table = dataset.get_data()   # TODO: check for Table (get_table?)

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
