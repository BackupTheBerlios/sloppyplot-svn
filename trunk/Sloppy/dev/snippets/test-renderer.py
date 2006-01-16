
from Sloppy.Gtk.pwconnect import *
import gtk


from Sloppy.Lib.Props import *
from Sloppy.Lib.Undo import UndoList
from Sloppy.Base.properties import *
from Sloppy.Gtk.proprenderer import *


class Recipe(HasProperties):
    name = Unicode()
    name_or_None = VP(Unicode, None)
    calories = VP(VRange(0,None), None)
    # works with VBMap as well!
    difficulty = VP({"easy":1, "average":2, "hard":3})

    rating = VP( VMap({'excellent': 0, 'ok': 1, 'bad': 2, 'awful': 3}),
                 default='ok')
    
    weight = Float(default=214.32)
    foodcolor = RGBColor('black')

    beverage = VP(["wine", "coke", "water"])

    is_delicious = Boolean(True)
    is_recommended = VP(Boolean,None, default=True)

    
    
recipe = Recipe(name="Toast Hawaii", calories=512, difficulty="average")
recipe.foodcolor=(0.0,1.0,0.3)

win = gtk.Window()




keys = ['name', 'weight', 'beverage', 'is_delicious', 'difficulty', 'rating']
my_model = gtk.ListStore(*([object]*len(keys)))    
treeview = gtk.TreeView(my_model)

clist = []
index = 0
for key in keys:
    column = gtk.TreeViewColumn(key)    
    cname = get_cname(recipe, key)
    connector = renderers[cname](recipe, key)
    column = connector.create(my_model, index)    
    treeview.append_column(column)    
    clist.append(connector)
    index += 1

# fill model
row = []
for key in keys:
    row.append( recipe.get_value(key) )
my_model.append(row)




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
