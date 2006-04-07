from Sloppy.Gtk import uihelper
from Sloppy.Base import globals
from Sloppy.Lib.Undo import UndoList, ulist

import sims


def gtk_init(app):
    
    a = uihelper.ActionWrapper('CreatePFC', "Create a SIMS profile from Dataset")
    a.connect(_cb_create_pfc)

    b = uihelper.ActionWrapper('CreateSPC', 'Create a SIMS spectrum from Dataset')
    b.connect(_cb_create_spc)

    app.register_actions([a,b])


#----------------------------------------------------------------------

def _cb_create_pfc(action):
    dslist = globals.app.selected_datasets
    project = globals.app.project

    ul = UndoList().describe("Create Profiles (PFC)")
    for ds in dslist:
        create_pfc(ds, undolist=ul)
    project.journal.append(ul)


def _cb_create_spc(action):
    dslist = globals.app.selected_datasets
    project = globals.app.project

    ul = UndoList().describe("Create Spectra (SPC)")
    for ds in dslist:
        self.create_spc(ds, undolist=ul)
    project.journal.append(ul)


#----------------------------------------------------------------------
