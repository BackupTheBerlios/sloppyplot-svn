
from Sloppy.Base.plugin import PluginRegistry

import main

import gtk



class PeakFinder_GTKDialog(gtk.Dialog):

    def __init__(self, app):
        self.app = app


    def init(self,):
        gtk.Dialog.__init__(self, "Peak Finder", None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        


PluginRegistry["PeakFinder_GTKDialog"] = PeakFinder_GTKDialog

        

