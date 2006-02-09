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

# $HeadURL$
# $Id$


"""
Provides class for docking functionality.

Dock - a container for dockbooks
Dockbook - a container for dockables
Dockable - a VBox that can be docked

@note: For an implementation of this package with resizable dockbooks,
take a look at SVN revision 135.
"""



try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass

import gtk, gobject
from Sloppy.Base import config


DockRegistry = []


class Dockable( gtk.VBox ):

    TARGET_TYPE_TEXT = 80
    dnd_from_label = [ ("text/plain", gtk.TARGET_SAME_APP, TARGET_TYPE_TEXT) ]

    def __init__(self, blurb, stock_id):
        gtk.VBox.__init__(self)
        
        self.blurb = blurb
        self.stock_id = stock_id

        self.dockbook = None
        
        menu_button = gtk.Button('*')
        menu_button.unset_flags(gtk.CAN_FOCUS)
        menu_button.set_relief(gtk.RELIEF_NONE)
        menu_button.show()

#         image = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PREVIOUS, gtk.ICON_SIZE_MENU)
#         menu_button.add(image)
#         image.show()

        close_button = gtk.Button()
        close_button.unset_flags(gtk.CAN_FOCUS)
        close_button.set_relief(gtk.RELIEF_NONE)
        close_button.show()

        close_button.connect("clicked", self.close_button_clicked)

        image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        close_button.add(image)
        image.show()

        title_label = gtk.Label(self.blurb)
        title_label.unset_flags(gtk.CAN_FOCUS)
        title_label.show()

        title_box = gtk.HBox()
        title_box.pack_start( title_label, True, True )
        title_box.pack_end( close_button, False, True )
        #title_box.pack_end( menu_button, False, True )
        title_box.show()

        event_box = gtk.EventBox()
        event_box.add(title_box)
        event_box.set_border_width(2)
        event_box.set_data("dockable", self)
        event_box.show()
        
        self.pack_start(event_box, False)

        # set up dnd for title_label
        event_box.drag_source_set(gtk.gdk.BUTTON1_MASK|gtk.gdk.BUTTON2_MASK,
                                    self.dnd_from_label,
                                    gtk.gdk.ACTION_MOVE)
        #event_box.drag_source_set_icon_pixbuf(self.get_drag_pixbuf())
        event_box.drag_source_set_icon_stock(self.stock_id)

        self.drag_dest_set( gtk.DEST_DEFAULT_ALL,
                            self.dnd_from_label,
                            gtk.gdk.ACTION_MOVE )
        self.connect("drag-drop", self.dnd_drag_drop)
        self.set_data("dockable", self)

        self.event_box = event_box
        

    def add(self, widget,expand=True,fill=True):
        if len(self.get_children()) == 1:
            gtk.VBox.pack_start(self, widget, expand, fill)
        else:
            raise RuntimeError("Can't add more than one non-internal object to a Dockable.")
        

        
    def get_menu_widget(self):
        image = gtk.image_new_from_stock(self.stock_id, gtk.ICON_SIZE_MENU)
        image.show()
        label = gtk.Label(self.blurb)
        label.show()

        hbox = gtk.HBox()
        hbox.pack_start(image,False,True)
        hbox.pack_start(label,True,True)
        hbox.show()

        return hbox


    def get_tab_widget(self):
        image = gtk.image_new_from_stock(self.stock_id, gtk.ICON_SIZE_MENU)
        image.show()
       
        event_box = gtk.EventBox()
        event_box.add(image)
        event_box.set_data("dockable", self)
        event_box.show()

        event_box.drag_source_set(gtk.gdk.BUTTON1_MASK,
                              self.dnd_from_label,
                              gtk.gdk.ACTION_MOVE)
        event_box.drag_source_set_icon_stock(self.stock_id)
    
        return event_box

    def get_drag_pixbuf(self):
        pass

    def close_button_clicked(self, sender):
        self.dockbook.remove(self)

    def dnd_drag_drop(self, sender, context, x, y, timestamp):
        return self.dockbook.tab_dnd_drag_drop(sender, context, x, y, timestamp)

        
        
gobject.type_register(Dockable)





class Dockbook( gtk.Notebook ):

    __gsignals__ = {
        'dockable-added' : (gobject.SIGNAL_RUN_FIRST ,
                            gobject.TYPE_NONE,
                            (gobject.TYPE_OBJECT,)),
        'dockable-removed' : (gobject.SIGNAL_RUN_FIRST ,
                              gobject.TYPE_NONE,
                              (gobject.TYPE_OBJECT,)),
        'dockable-reordered' : (gobject.SIGNAL_RUN_FIRST ,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_OBJECT,))
        }

    def __init__(self):
        gtk.Notebook.__init__(self)

        self.dock = None
        self.uimanager = None
        
        self.popup_enable()
        self.set_scrollable(True)
        
        self.connect('dockable-added', self.dockable_added)
        self.connect('dockable-removed', self.dockable_removed)
        
        self.dockbooks = []
        
        self.drag_dest_set( gtk.DEST_DEFAULT_ALL,
                            Dockable.dnd_from_label,
                            gtk.gdk.ACTION_MOVE )
        self.connect("drag-drop", self.notebook_dnd_drag_drop)
        
        
    def add(self, dockable, position=-1):
        assert( isinstance(dockable, Dockable) )
        assert( dockable.dockbook == None )

        tab_widget = dockable.get_tab_widget()
        menu_widget = dockable.get_menu_widget()
        
        if position == -1:
            self.append_page_menu(dockable, tab_widget, menu_widget)
        else:
            self.insert_page_menu(dockable, tab_widget, menu_widget, position)

        dockable.show()
        dockable.dockbook = self

        tab_widget.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                                 Dockable.dnd_from_label,
                                 gtk.gdk.ACTION_MOVE)
        tab_widget.connect("drag-drop", self.tab_dnd_drag_drop)
        tab_widget.set_data("dockbook", self)

        self.emit('dockable-added', dockable)

    def remove(self, dockable, clean_up=True):
        dockable.dockbook = None
        gtk.Notebook.remove(self, dockable)
        self.emit('dockable-removed', dockable)
        if clean_up is True and len(self.get_children()) == 0:
            self.dock.remove_book(self)
            

    def dockable_added(self, sender, dockable): self.update_tabs(True)
    def dockable_removed(self, sender, dockable):  self.update_tabs(False)

    def update_tabs(self, added):
        n = self.get_n_pages()
        if n == 1:
            self.set_show_tabs(False)
        elif n == 2 and added is True:
            self.set_show_tabs(True)


    def tab_dnd_drag_drop(self, dest_widget, context, x, y, time):

        source = context.get_source_widget().get_data("dockable")
        dest_widget = dest_widget.get_data("dockable")

        if isinstance(source, Dockable):
            index = self.page_num(dest_widget)
            clean_up = not source.dockbook == self
            source.dockbook.remove(source, clean_up=clean_up)
            self.add(source, index)
            self.set_current_page(index)

            return True

        return False

    def notebook_dnd_drag_drop(self, dest_widget, context, x, y, time):

        source = context.get_source_widget().get_data("dockable")

        if isinstance(source, Dockable):
            clean_up = not source.dockbook == self
            source.dockbook.remove(source, clean_up=clean_up)
            self.add(source, -1)
            self.set_current_page(-1)
        
            

gobject.type_register(Dockbook)




class Dock( gtk.VBox ):


    __gsignals__ = {
        'book-added' : (gobject.SIGNAL_RUN_FIRST , gobject.TYPE_NONE,
                        (gobject.TYPE_OBJECT,)),
        'book-removed' : (gobject.SIGNAL_RUN_FIRST , gobject.TYPE_NONE,
                          (gobject.TYPE_OBJECT,))
        }


    def __init__(self):
        gtk.VBox.__init__(self, False) # False? How to avoid spacing?

        self.dockbooks = []
        
        self.separator = self.separator_new()
        self.pack_start(self.separator,False)
        self.separator.show()
        
        self.connect('book-added', self.book_added)
        self.connect('book-removed', self.book_removed)
        
        
    def add(self, item):
        if isinstance(item, Dockable):
            if len(self.dockbooks) == 0:
                book = Dockbook()
                self.add_book(book)
            book = self.dockbooks[0]
            book.add(item)
        elif isinstance(item, Dockbook):
            self.add_book(item)
        else:
            raise TypeError("Item is of type %s but should be either Dockable or Dockbook" % type(item))


    def add_book(self, dockbook, index=-1):
        assert( isinstance(dockbook, Dockbook) )
        assert( dockbook.dock == None )

        old_length = len(self.dockbooks)
        if (index >= old_length) or (index < 0):
            index = old_length

        dockbook.dock = self
        self.dockbooks.insert(index, dockbook)

        if old_length == 0:
            separator = self.separator_new()            
            self.pack_end(separator, False, False)            
            self.pack_end(dockbook, True, True)
            separator.show()
        else:
            gtk.VBox.add(self, dockbook)
            self.reorder_child(dockbook, index)

        dockbook.show()

        self.emit('book-added', dockbook)


    def remove_book(self, dockbook):
        old_length = len(self.dockbooks)
        index = self.dockbooks.index(dockbook)

        dockbook.dock = None
        self.dockbooks.remove(dockbook)

        if old_length == 1:
            children = self.get_children()
            separator = children[2]
            gtk.VBox.remove(self, separator)
            gtk.VBox.remove(self, dockbook)
        else:
            self.remove(dockbook)
            children = self.get_children()
            if len(children) == 2:
                self.remove(children[-1])
        self.emit('book-removed', dockbook)


    def book_added(self, sender, dockbook):
        pass

    def book_removed(self, sender, dockbook):
        pass

    def separator_new(self):
        
        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_OUT)
        frame.show()

        event_box = gtk.EventBox()
        event_box.set_name("dock-separator")
        event_box.set_size_request(-1, 8)
        event_box.add(frame)

        event_box.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                                 Dockable.dnd_from_label,
                                 gtk.gdk.ACTION_MOVE)

        event_box.connect("drag-leave", self.separator_dnd_drag_leave)
        event_box.connect("drag-motion", self.separator_dnd_drag_motion)
        event_box.connect("drag-drop", self.separator_dnd_drag_drop)
        
        return event_box

    def separator_dnd_drag_leave(self, sender, context, time):
        sender.modify_bg(gtk.STATE_NORMAL, None)

    def separator_dnd_drag_motion(self, sender, context, x, y, time):
        color = gtk.gdk.Color(65535,0,0)
        sender.modify_bg(gtk.STATE_NORMAL, color)

    def separator_dnd_drag_drop(self, sender, context, x, y, time):
        source = context.get_source_widget().get_data("dockable")    
        separator_index = self.get_children().index(sender)

        if separator_index == 0:
            index = 0
        else:
            index = -1

        book = Dockbook()
        source.dockbook.remove(source)
        book.add(source)
        self.add_book(book, index)        

    def foreach(self, callback, *args, **kwargs):
        for dockbook in self.dockbooks:
            for child in dockbook.get_children():
                callback(child, *args, **kwargs)

    def get_positions(self):
        def do_loop(item):
            rv = []
            print 
            print item.get_children()
            print
            for child in item.get_children():                
                if isinstance(child, gtk.VPaned):
                    rv.append(child.get_position())
                    next = do_loop(child)
                    if len(next) > 0:
                        rv.append(next)
                else:
                    pass
            return rv

        return do_loop(self)    

gobject.type_register(Dock)


       

#==============================================================================
    
#==============================================================================

def test():
    win = gtk.Window()
    dock = Dock()

    dockbook = Dockbook()
    dock.add_book(dockbook)

    dockable = Dockable('d1', gtk.STOCK_UNDO)
    b = gtk.Button("Eins")
    b.show()
    dockable.pack_end(b)
    dockbook.add(dockable)
    b1 = b

    # size test: set minium size of a dockable
    dockable.set_size_request(200,120)
    
    dockable = Dockable('d2', gtk.STOCK_REDO)
    b = gtk.Button("Zwei")
    b.show()
    dockable.pack_end(b)
    dockbook.add(dockable)
    b2 = b

    # size test: set minium size of a dockable
    dockable.set_size_request(200,120)
    
    dockbook = Dockbook()
    dock.add_book(dockbook)

    dockable = Dockable('d4', gtk.STOCK_UNDO)
    dockbook.add(dockable)

    dockbook = Dockbook()
    dock.add_book(dockbook)

    dockable = Dockable('d5', gtk.STOCK_UNDO)
    dockbook.add(dockable)
    dockable = Dockable('d6', gtk.STOCK_REDO)
    dockbook.add(dockable)
    dockable = Dockable('d7', gtk.STOCK_REDO)
    dockbook.add(dockable)


    win.add(dock)
    dock.show()
    win.show()

    def print_child(child):
        print "+", child
        print " ", child.allocation.height
        def print_grandchild(grandchild):
            print "  -", grandchild
        child.foreach( print_grandchild )

    win.connect("destroy", gtk.main_quit)
    win.set_size_request(240,-1)
    win.set_default_size(300,500)

    # pseudo app
    class A:
        toolwindow = dock
    class B:
        window = A()
        
    config.build_all(B())
    
    gtk.main()


if __name__ == "__main__":
    test()

