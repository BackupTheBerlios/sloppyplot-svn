
from Sloppy.Gtk.pwconnect import *
import gtk

from Sloppy.Lib.Props import *
from Sloppy.Lib.Undo import UndoList
from Sloppy.Base.properties import *
from Sloppy.Gtk.proprenderer import *
from Sloppy.Gtk.widget_factory import *

    
class Recipe(HasProperties):
    name = Unicode()
    name_or_None = VP(Unicode, None)
#    calories = VP(VRange(0,None), None)
    difficulty = VP(["easy", "average", "hard"])
    rating = VP(['ok', 'not so good', 'bad'])
    weight = Float(default=214.32)
#    foodcolor = RGBColor('black')
    beverage = VP(["wine", "coke", "water"])
    is_delicious = Boolean(True)
    is_recommended = VP(Boolean,None, default=True)


class CookBook(HasProperties):
    recipelist = VProperty( VList(VInstance(Recipe)) )
   

cookbook = CookBook()
cookbook.recipelist = [Recipe(name="Toast Hawaii", difficulty="average"),
                       Recipe(name="Salat Special", difficulty="hard")]


#------------------------------------------------------------------------------
factory = CTreeViewFactory(cookbook, 'recipelist')
factory.add_columns(Recipe().get_keys())
treeview = factory.create_treeview()
factory.check_in()
#------------------------------------------------------------------------------

win = gtk.Window()
win.add(treeview)
win.show_all()

def do_quit(udata, factory):
    factory.check_out()
    print cookbook.recipelist[0].get_values()
    print cookbook.recipelist[1].get_values()    
    gtk.main_quit()
    
win.connect("destroy", do_quit, factory)
#------------------------------------------------------------------------------
factory = CWidgetFactory(cookbook.recipelist[0])
factory.add_keys(Recipe().get_keys())
vbox = factory.create_vbox()
factory.check_in()
#------------------------------------------------------------------------------
win = gtk.Window()
win.add(vbox)
win.show_all()

gtk.main()
