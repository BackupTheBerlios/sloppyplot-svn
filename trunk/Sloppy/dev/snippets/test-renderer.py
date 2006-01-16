
from Sloppy.Gtk.pwconnect import *
import gtk

from Sloppy.Lib.Props import *
from Sloppy.Lib.Undo import UndoList
from Sloppy.Base.properties import *
from Sloppy.Gtk.proprenderer import *


class Recipe(HasProperties):
    name = Unicode()
    name_or_None = VP(Unicode, None)
#    calories = VP(VRange(0,None), None)
    # works with VBMap as well!
    difficulty = VP({"easy":1, "average":2, "hard":3})
    rating = VP( VMap({'excellent': 0, 'ok': 1, 'bad': 2, 'awful': 3}), default='ok')
    weight = Float(default=214.32)
#    foodcolor = RGBColor('black')
    beverage = VP(["wine", "coke", "water"])
    is_delicious = Boolean(True)
    is_recommended = VP(Boolean,None, default=True)
   
    
recipes = [Recipe(name="Toast Hawaii", difficulty="average"),
           Recipe(name="Salat Special", difficulty=3)]

#------------------------------------------------------------------------------

class CRendererFactory:

    def __init__(self, container):
        # TODO: container is a class instance. What if this instance
        # TODO: gets removed?  It would be good if a renderer was
        # TODO: using the container that is located in its row.
        self.container = container 
        self.keys = []
        self.model = None
        self.treeview = None


    def add_keys(self, *keys):
        for key in keys:
            if isinstance(key, basestring):
                self.keys.append(key)
            elif isinstance(key, (list,tuple)):
                self.keys.extend(key)
            else:
                raise TypeError("String or tuple required.")

          
    def create_treeview(self):
        model = gtk.ListStore(*([object]*(len(self.keys) + 1)))    
        treeview = gtk.TreeView(model)        

        index = 1
        print self.keys
        for key in self.keys:
            column = gtk.TreeViewColumn(key)
            cname = get_cname(self.container, key)
            renderer = renderers[cname](self.container, key)
            column = renderer.create(model, index)
            treeview.append_column(column)    
            index += 1
            
        self.treeview = treeview
        return self.treeview


    def check_in(self, itemlist):
        # fill model
        model = self.treeview.get_model()
        for item in itemlist:
            row = []
            for key in self.keys:
                row.append( item.get_value(key) )
            model.append( [item] + row )
        

    def check_out(self, undolist=[]):
        # TODO: implement undolist
        # TODO: We could also allow reordering of the list !
        model = self.treeview.get_model()
        iter = model.get_iter_first()
        while iter is not None:
            n = 1
            owner = model.get_value(iter, 0)            
            for key in self.keys:
                value = model.get_value(iter, n)
                owner.set_value(key, value)
                n += 1
            iter = model.iter_next(iter)
                

#------------------------------------------------------------------------------

class CWidgetFactory:

    def __init__(self, container):
        self.container = container
        self.keys = []

    def add_keys(self, *keys):
        for key in keys:
            if isinstance(key, basestring):
                self.keys.append(key)
            elif isinstance(key, (list,tuple)):
                self.keys.extend(key)
            else:
                raise TypeError("String or tuple required.")
    
    def create_vbox(self):
        vbox = gtk.VBox()

        clist = []
        for key in self.keys:
            connector = new_connector(self.container, key)
            vbox.add(connector.create_widget())
            clist.append(connector)
        self.clist = clist

        return vbox

    def check_in(self, item):
        # item is currently ignored
        for connector in self.clist:
            connector.check_in()

    def check_out(self, undolist=[]):
        ul = UndoList()    
        for c in clist:
            c.check_out(undolist=ul)
        undolist.append(ul)       

            
#------------------------------------------------------------------------------
factory = CRendererFactory(Recipe())
factory.add_keys(Recipe().get_keys())
treeview = factory.create_treeview()
factory.check_in(recipes)

win = gtk.Window()
win.add(treeview)
win.show_all()

def do_quit(udata, factory):
    factory.check_out()
    print recipes[0].get_values()
    print recipes[1].get_values()
    
    gtk.main_quit()
    
win.connect("destroy", do_quit, factory)
#------------------------------------------------------------------------------

factory = CWidgetFactory(Recipe())
factory.add_keys(Recipe().get_keys())
vbox = factory.create_vbox()
factory.check_in(recipes[0])

win = gtk.Window()
win.add(vbox)
win.show_all()

#------------------------------------------------------------------------------
gtk.main()
