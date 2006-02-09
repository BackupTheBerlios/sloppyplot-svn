
from Sloppy.Lib.Undo import UndoList, ulist
from Sloppy.Base import globals, dataio
import os.path



def import_datasets(project, filenames, template, undolist=None):
    """
    Import datasets from a list of given `filenames` into the
    given `project`. The given importer `template` can either
    be a template name (a string) or an ImporterTemplate object.    
    """
    
    app = globals.app

    if undolist is None:
        undolist = project.journal

    if isinstance(template, basestring): # template key
        template = globals.import_templates[template]

    # To ensure a proper undo, the Datasets are imported one by one
    # to a temporary dict.  When finished, they are added as a whole.
    new_datasets = []

    n = 0.0
    N = len(filenames)
    app.progress(0)        
    for filename in filenames:
        app.status_msg("Importing %s" % filename)                       
        try:
            importer = template.new_instance()                
            ds = importer.read_dataset_from_file(filename)
        except dataio.ImportError, msg:
            app.error_msg(msg)
            continue
        except error.UserCancel:
            app.error_msg("Import aborted by user")
            continue

        root, ext = os.path.splitext(os.path.basename(filename))
        ds.key = utils.encode_as_key(root)

        new_datasets.append(ds)
        n+=1
        app.progress(n/N)

    app.progress(100)

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

    app.progress(-1)
    #app.status_message(msg)
