# This file is part of SloppyPlot, a scientific plotting tool.
# Copyright (C) 2005 Niklas Volbers
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# $HeadURL: file:///home/nv/sloppysvn/trunk/Sloppy/src/Sloppy/Base/project.py $
# $Id: project.py 430 2005-08-03 20:07:56Z nv $


from Sloppy.Base.progress import ProgressList, AbortIteration


import gtk
import time

import uihelper
import os.path


class GtkProgressList(ProgressList, gtk.Window):

    def __init__(self, objects):
        gtk.Window.__init__(self)
        self.set_modal(True)
        self.set_size_request(480,320)
        
        ProgressList.__init__(self, objects)

        vbox = gtk.VBox()

        # set up progressbar
        bar = gtk.ProgressBar()
        bar.set_fraction(0.0)
        bar.show()
        
        # set up listview with a model := (filename, status)
        model = gtk.ListStore(str, str)
        listview = gtk.TreeView(model)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("filename", cell)
        column.set_cell_data_func(cell, self.render_filename)
        listview.append_column(column)
        column = gtk.TreeViewColumn('Status', cell, text=1)
        listview.append_column(column)
        listview.show()

        sw = uihelper.add_scrollbars(listview)
        sw.show()

        # the scrolled window (sw) with the listview is put into an expander widget
        expander = gtk.Expander("Details")
        expander.set_expanded(False)
        expander.add(sw)
        #expander.connect("notify::expanded", lambda e,p: self.check_resize())
        expander.show()

        # set up button box
        btn_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        btn_cancel.show()

        btn_ok = gtk.Button(stock=gtk.STOCK_OK)
        btn_ok.show()
        
        btnbox = gtk.HButtonBox()
        btnbox.add(btn_cancel)
        btnbox.add(btn_ok)        
        btnbox.set_layout(gtk.BUTTONBOX_END)
        btnbox.show()

        # initially, btn_ok is disables.
        btn_cancel.connect("clicked", (lambda sender: self.abort()))

        btn_ok.connect("clicked", (lambda sender: self.destroy()))
        btn_ok.set_sensitive(False)        

        # stack everything into a vbox.
        #vbox.pack_start(listview, False, True, padding=5)
        vbox.pack_start(bar, False, True, padding=5)
        vbox.pack_start(expander, True, True, padding=5)
        vbox.pack_start(sw, True, True, padding=5)
        vbox.pack_end(btnbox,False,True, padding=5)
        vbox.show()
                
        self.add(vbox)
        self.show()

        # fill model with string names
        for object in self.objects:
            model.append( (object,"") )
        self.iter = None

        while gtk.events_pending():
            gtk.main_iteration()

        # save some variables for further reference
        self.model = model
        self.bar = bar
        self.btn_cancel = btn_cancel
        self.btn_ok = btn_ok
        self.expander = expander


    #----------------------------------------------------------------------
    # gtk specific

    def render_filename(self, column, cell, model, iter):
        value = model.get_value(iter, 0)
        cell.set_property('text', os.path.basename(value))

    def stop_iteration(self):
        self.btn_cancel.set_sensitive(False)
        self.btn_ok.set_sensitive(True)
        while gtk.events_pending():
            gtk.main_iteration()

    #----------------------------------------------------------------------
    # implemenation of base class method

    def next(self):
        # update progress bar
        self.bar.set_fraction( (self.index+1) / float(self.maxindex) )
        self.bar.set_text("")
        while gtk.events_pending():
            gtk.main_iteration()

        try:
            name = ProgressList.next(self)
        except StopIteration:
            self.stop_iteration()
            raise
        
        # update listview text
        if self.iter is None:
            self.iter = self.model.get_iter_first()
        else:
            self.iter = self.model.iter_next(self.iter)
        self.model.set_value( self.iter, 1, "IN PROGRESS" )
        self.bar.set_text(self.objects[self.index])        
        while gtk.events_pending():
            gtk.main_iteration()

        return name
    

    def fail(self, msg=None):
        self.model.set_value( self.iter, 1, "FAILED (%s)" % msg or "unknown error" )
        while gtk.events_pending():
            gtk.main_iteration()
        self.is_successful = False

    def succeed(self):
        self.model.set_value( self.iter, 1, "OK" )
        while gtk.events_pending():
            gtk.main_iteration()

    def finish(self):
        if self.is_successful is True:            
            self.destroy()
        else:
            self.expander.set_expanded(True)

    def abort(self):
        ProgressList.abort(self)
        self.model.set_value( self.iter, 1, "ABORTED" )
        self.expander.set_expanded(True)
        self.stop_iteration()
        
        



def test():

    filenames = ['file A', 'file B', 'file C',
                 'file D', 'file E', 'file F',
                 'file G', 'file H', 'file I',
                 'file J', 'file K', 'file L']

    try:
        pi = GtkProgressList(filenames)
        for filename in pi:
            print filename
            time.sleep(0.3)
            pi.succeed()
        pi.finish()
    except AbortIteration:
        print "It was aborted..."

    gtk.main()

    
if __name__ == "__main__":
    test()
