
from Sloppy.Base.plugin import PluginRegistry
from Sloppy.Lib.Props import *

import main

import gtk



  

class Dialog(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self, "Peak Finder", None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        vbox = gtk.VBox()

        # Line (=> cx and cy will be automatically determined)
        ctl_line = gtk.ComboBox()
        ctl_line.show()
        vbox.add(ctl_line)
        
        # threshold
        ctl_threshold = gtk.Entry()
        ctl_threshold.show()
        vbox.add(ctl_threshold)
        
        # accuracy
        ctl_accuracy = gtk.Entry()
        ctl_accuracy.show()
        vbox.add(ctl_accuracy)
        
        # max. nr. of points before aborting.

        vbox.show()
        self.vbox.add(vbox)

    
class DialogBuilder(gtk.Dialog):

    def __init__(self, app):
        self.app = app

    def new_dialog(self):
        return Dialog()
        

    def run(self):
        return gtk.Dialog.run(self)

    

PluginRegistry["PeakFinder::GTK::DialogBuilder"] = DialogBuilder

        

