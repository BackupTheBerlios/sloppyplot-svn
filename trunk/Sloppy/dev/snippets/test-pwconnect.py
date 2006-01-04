
import pwconnect
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
    
    
recipe = Recipe(name="Toast Hawaii", calories=512, difficulty="average")
recipe.foodcolor=(0.0,1.0,0.3)
win = gtk.Window()


def determine_connector(owner, key):
    prop = owner.get_prop(key)
    vlist = prop.validator.vlist

    while len(vlist) > 0:
        v = vlist[0]
        if isinstance(v, VMap):
            return pwconnect.connectors['Map'](owner, key)
        elif isinstance(v, (VUnicode,VInteger,VFloat,VString)):
            return pwconnect.connectors['Unicode'](owner, key)
        elif isinstance(v, VRange):
            return pwconnect.connectors['Range'](owner, key)
        elif isinstance(v, VRGBColor):
            return pwconnect.connectors['RGBColor'](owner, key)

        vlist.pop(0)

    raise RuntimeError("No connector found for property.")
            
    
    
vbox = gtk.VBox()

clist = []
for key in recipe.get_props().keys():
    connector = determine_connector(recipe, key)
    vbox.add(connector.create_widget())
    connector.check_in()
    clist.append(connector)

win.add(vbox)
win.show_all()

def do_quit(udata, clist):

    print "Values before:"
    print recipe.get_values()

    print
    print "Values after:"
    ul = UndoList()    
    for c in clist:
        c.check_out(undolist=ul)
    print recipe.get_values()

    print "Undoing: "
    ul.execute()
    print recipe.get_values()

    gtk.main_quit()
win.connect("destroy", do_quit, clist)

gtk.main()
