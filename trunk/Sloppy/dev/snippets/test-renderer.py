
from Sloppy.Gtk.pwconnect import *
import gtk


from Sloppy.Lib.Props import *
from Sloppy.Lib.Undo import UndoList
from Sloppy.Base.properties import *



class Recipe(HasProperties):
    name = Unicode()
    name_or_None = Property(Unicode, None)
    calories = Property(VRange(0,None), None)
    # works with VBMap as well!
    difficulty = Property({"easy":1, "average":2, "hard":3})

    weight = Float(default=214.32)
    foodcolor = RGBColor('black')

    beverage = Property(["wine", "coke", "water"])

    is_delicious = Boolean(True)
    is_recommended = Property(Boolean,None, default=True)

    
    
recipe = Recipe(name="Toast Hawaii", calories=512, difficulty="average")
recipe.foodcolor=(0.0,1.0,0.3)

win = gtk.Window()

    
my_model = gtk.ListStore(str)
treeview = gtk.TreeView(my_model)

clist = []
index = 0
for key in ['name','foodcolor']:#recipe.get_props().keys():
    column = gtk.TreeViewColumn(key)    
    connector = new_connector(recipe, key)
    connector.create_renderer(my_model, index)
    
    cell = connector.widget
    column.pack_start(cell)       
    column.set_attributes(cell, **connector.get_renderer_attributes())
    treeview.append_column(column)
    
##    connector.check_in()    
    clist.append(connector)
    index += 1

# fill model
my_model.append((recipe.name,recipe.foodcolor))

win.add(treeview)
win.show_all()

def do_quit(udata, clist):

    print "Values before:"
    print recipe.get_values()

    print
    print "Values after:"
    ul = UndoList()    
##    for c in clist:
##        c.check_out(undolist=ul)
##    print recipe.get_values()

##    print "Undoing: "
##    ul.execute()
    print recipe.get_values()

    gtk.main_quit()
win.connect("destroy", do_quit, clist)

gtk.main()
