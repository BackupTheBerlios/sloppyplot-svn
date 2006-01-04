
import pwconnect
import gtk


from Sloppy.Lib.Props import *
from Sloppy.Lib.Undo import UndoList

class Recipe(HasProperties):
    name = Unicode()
    name_or_None = Property(Unicode, None)
    calories = Property(VRange(0,None), None)
    
    
recipe = Recipe(name="Toast Hawaii", calories=512)

win = gtk.Window()

connector = pwconnect.connectors['Range'](recipe, 'calories')
win.add(connector.create_widget())
connector.check_in()

win.show_all()

def do_quit(udata):
    ul = UndoList()
    connector.check_out(undolist=ul)
    print "New value: ", connector.get_value()
    ul.execute()
    print "Undoing will yield: ", connector.get_value()
    gtk.main_quit()
win.connect("destroy", do_quit)

gtk.main()
