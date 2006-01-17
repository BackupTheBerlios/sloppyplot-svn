
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


class CookBook(HasProperties):
    recipelist = VProperty( VList(VInstance(Recipe)) )
   

cookbook = CookBook()
cookbook.recipelist = \
                    [Recipe(name="Toast Hawaii", difficulty="average"),
                     Recipe(name="Salat Special", difficulty=3)]


#------------------------------------------------------------------------------

class CRendererFactory:

    def __init__(self, listowner, listkey):
        self.listowner = listowner 
        self.listkey = listkey

        prop = listowner.get_prop(listkey)
        validators = [v for v in prop.validator.vlist if isinstance(v, VList)]
        if len(validators) == 0:
            raise TypeError("%s.%s must be a List.",
                            (listowner.__class__.__name__, listkey))        
        else:
            vlist = validators[0]
        item_validators = [v for v in vlist.item_validator.vlist if isinstance(v, VInstance)]
        if len(item_validators) == 0:
            raise TypeError("%s.%s must be limited to a certain class instance (VInstance)." %
                            (listowner.__class__.__name__, listkey))
        else:
            self.container = item_validators[0].instance()
        
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


    def check_in(self):
        itemlist = self.listowner.get_value(self.listkey)
        model = self.treeview.get_model()
        for item in itemlist:
            row = []
            for key in self.keys:
                row.append( item.get_value(key) )
            model.append( [item] + row )

        self.old_list = itemlist
        

    def check_out(self, undolist=[]):

        def check_out_row(owner, iter, undolist=[]):
            n = 1
            adict = {}
            for key in self.keys:
                adict[key]=model.get_value(iter, n)
                n += 1
            adict['undolist'] = ul
            uwrap.smart_set(owner, **adict)

        new_list = []
        model = self.treeview.get_model()        
        iter = model.get_iter_first()
        while iter is not None:
            owner = model.get_value(iter, 0)
            check_out_row(owner, iter, undolist=ul)
            new_list.append(owner)
            iter = model.iter_next(iter)
        
        if self.old_list != new_list:        
            uwrap.set(self.listowner, listkey, new_list, undolist=ul)
            self.old_list = new_list


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
factory = CRendererFactory(cookbook, 'recipelist')
factory.add_keys(Recipe().get_keys())
treeview = factory.create_treeview()
factory.check_in()
#------------------------------------------------------------------------------

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
#factory = CWidgetFactory(Recipe())
#factory.add_keys(Recipe().get_keys())
#vbox = factory.create_vbox()
#factory.check_in()
#------------------------------------------------------------------------------
#win = gtk.Window()
#win.add(vbox)
#win.show_all()

gtk.main()
