
# sample code that shows how to load a glade file
# and extract a simple widget from it

import gtk
import gtk.glade


filename = "layer_editor.glade"
widgetname = 'container_axes'

tree = gtk.glade.XML(filename, widgetname)
# skip signal connect
# dic = {"on_button1_clicked": on_button1_clicked}
# tree.signal_autoconnect(dic)
#
widget = tree.get_widget(widgetname)

win = gtk.Window()
win.connect("destroy", gtk.main_quit)

win.add(widget)
win.show()
gtk.main()
