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

# $HeadURL: file:///home/nv/sloppysvn/trunk/Sloppy/src/Sloppy/Gtk/gtkutils.py $
# $Id: gtkutils.py 435 2005-08-04 16:30:05Z nv $


import logging
logger = logging.getLogger('Gtk.gtkutils')


import gtk, gobject



def create_buttonbox(list):
        
    """ A helper function that returns a gtk.HBox containing buttons
    by providing a simple list of the form:
    
    [("btn1", cb_btn1), ("btn2", cb_btn2)]
    """
        
    buttonbox = gtk.HBox()
    for label, func in list:
        button = gtk.Button()
        button.set_label(label)
        button.connect("clicked", func)
        button.show()
        buttonbox.pack_start(button, expand=gtk.FALSE, fill=gtk.FALSE)
        buttonbox.show()
    return buttonbox


def create_entry_with_label(label):
    " Returns tuple (entry, label). Both widgets' show() method is called. "
    entry = gtk.Entry()
    entry.show()
    label = gtk.Label(label)
    label.show()
    return (entry, label)

def create_hbox_with_widgets(widgets):
    """
    The widgets will be added to a newly created hbox which is returned.
    `widgets` may be a list/tuple or a single item.
    """
    if not isinstance(widgets, (list,tuple)):
        widgets = [widgets]
        
    hbox = gtk.HBox()
    for widget in widgets:
        hbox.pack_end(widget)
    hbox.show()

    return hbox

def create_xpm_combobox( xpm_prefix, xpm_count, text_list = None):

    """ A helper function that returns a gtk.ComboBox with xpm_count rows.

    The first column show the pixmap from the gfx path with the name
    xpm_prefix + n, where n is the two-digit number.  If
    e.g. xpm_prefix='ps' and xpm_count=3, the pixmaps are loaded from
    'ps00.xpm','ps01.xpm' and 'ps02.xpm'.

    The second column is only shown if text_list is given and contains
    the descriptions of the pixmaps.  If the number of list elements
    is less than the xpm_count, an exception is raised.

    combobox = create_xpm_combobox( xpm_prefix='ps',5,text_list=None )
    combobox = create_xpm_combobox( xpm_prefix='ps',2,text_list=['first','second'] )
    """

    # check if text_list is valid
    if (text_list) and (len(text_list) < xpm_count):
        raise
    
    # create combo
    if text_list:
        store = gtk.ListStore( gtk.gdk.Pixbuf, str )
    else:
        store = gtk.ListStore( gtk.gdk.Pixbuf )            
    combobox = gtk.ComboBox( store )
        
    # first column is the pixmap with a fixed size
    cell = gtk.CellRendererPixbuf()
    cell.set_property( 'xalign', 0.0 )
    cell.set_property( 'width', 16 )
    cell.set_property( 'height', 16 )        
    combobox.pack_start( cell, True )
    combobox.add_attribute( cell, 'pixbuf', 0 )

    # the second column is optional, the text
    if text_list:
        cell = gtk.CellRendererText()
        cell.set_property( 'xalign', 0.0 )
        combobox.pack_start( cell, True )
        combobox.add_attribute( cell, 'text', 1 )

    # add pixmaps        
    for i in range( xpm_count ):
        try:
            pb = gtk.gdk.pixbuf_new_from_file(
                gfx_path("%s%02d.xpm" % (xpm_prefix,i)) )
        except gobject.GError:
            logger.error("could not load pixbuf") # TODO: insert name
            pb = None
            
        if text_list:
            store.append( [pb, text_list[i]] )
        else:
            store.append( [pb] )

    return combobox


def create_combobox(entry_list):

    """ A helper function that returns a gtk.ComboBox with the given
    text entries, wrapped in the given number of columns."""
    
    combobox = gtk.combo_box_new_text()
    for entry in entry_list:
        combobox.append_text( entry )

    return combobox


def get_active_combotext(combobox):

    """ Returns the active text from a combobox with one column.
    Method taken from the PyGTK tutorial."""
    
    model = combobox.get_model()
    active = combobox.get_active()
    if active < 0:
        return None
    return model[active][0]



def create_popup(items):
    """
    This methode creates a popup widget given a list of items
    to appear in that menu.
    
    Call this method from a button_pressed event:

    object.connect('button_press_event', self.cb_button_pressed)

    where the event handler might look like this:

    def cb_button_pressed(self,widget,event):
        items = {
            'column 1' : (self.cb_quit, "extra information"),
            'column 2' : (self.cb_quit, "this is column 2", "with second arg"),
            'quit': (gtk.main_quit)
            }
        create_popup(items).popup(None,None,None,event.button,event.time)

    Additonal items in the value of the dictionary (e.g. "extra
    information") is passed to the corresponding method, in this case
    to self.cb_quit, which might look like this.

    def cb_quit(self,widget,extra_data):
        print "EXTRA DATA: ", extra_data
        gtk.main_quit()

    """
        
    menu = gtk.Menu()

    for (item_label,item) in items.iteritems():
        menu_item = gtk.MenuItem(item_label)
        menu.prepend(menu_item)
        if isinstance(item, tuple):
            menu_item.connect("activate", item[0], item[1:])
        else:
            menu_item.connect("activate", item)
        menu_item.show()

    return menu


def dialog_confirm_list(title, msg, objects):
    dialog = gtk.MessageDialog(parent = None,
                               flags = 0,
                               type = gtk.MESSAGE_QUESTION,
                               buttons = gtk.BUTTONS_OK_CANCEL,
                               message_format = msg)
    dialog.set_title(title)

    # list of objects
    model = gtk.ListStore(str)
    cell = gtk.CellRendererText()
    column = gtk.TreeViewColumn('object', cell)
    column.set_attributes(cell, text=0)
    tv = gtk.TreeView(model) ; tv.show()
    tv.append_column(column)
    tv.get_selection().set_mode(gtk.SELECTION_NONE)

    for object in objects:
        model.append((object.key,))

    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    sw.add(tv)
    sw.show()

    frame = gtk.Frame()
    frame.set_shadow_type(gtk.SHADOW_IN)
    frame.add(sw)

    dialog.vbox.add(frame)

    dialog.details = frame
    dialog.set_position(gtk.WIN_POS_CENTER)
    dialog.set_gravity(gtk.gdk.GRAVITY_CENTER)
    dialog.details.show()

    response = dialog.run()
    dialog.destroy()
    return response    


def dialog_confirm(title, msg):
    " Returns True/False. "
    dialog = gtk.MessageDialog(parent = None,
                               flags = 0,
                               type = gtk.MESSAGE_QUESTION,
                               buttons = gtk.BUTTONS_YES_NO,
                               message_format = msg)
    dialog.set_title(title)    
    
    response = dialog.run()
    dialog.destroy()
    if response == gtk.RESPONSE_YES:
        return True
    else:
        return False

def info_msg(msg):
    dialog = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_INFO,
                               buttons = gtk.BUTTONS_OK, message_format=msg)
    dialog.set_title("Info")
    response = dialog.run()
    dialog.destroy()

def error_msg(msg):
    dialog = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_ERROR,
                               buttons = gtk.BUTTONS_OK, message_format=msg)
    dialog.set_title("Error!")
    response = dialog.run()
    dialog.destroy()
    


def register_iconsets(imgdir, icon_info):
    import os
    iconfactory = gtk.IconFactory()
    stock_ids = gtk.stock_list_ids()
    for stock_id, file in icon_info.iteritems():
        # only load image files when our stock_id is not present
        if stock_id not in stock_ids:
            file = os.path.join(imgdir, file)
            print "loading image %s" % file
            pixbuf = gtk.gdk.pixbuf_new_from_file(file)
            iconset = gtk.IconSet(pixbuf)
            iconfactory.add(stock_id, iconset)
    iconfactory.add_default()


def register_all_png_icons(imgdir, prefix=""):
    """
    Register all svg icons in the Icons subdirectory as stock icons.
    The prefix is the prefix for the stock_id.
    """
    logger.debug("Trying to register png icons from dir '%s'" % imgdir)
    import glob, os
    filelist = map(lambda fn: ("%s%s" % (prefix, fn.split(os.path.sep)[-1][:-4]), fn), \
                   glob.glob(os.path.join(imgdir,'*.png')))
    
    iconfactory = gtk.IconFactory()
    stock_ids = gtk.stock_list_ids()
    for stock_id, file in filelist:
        # only load image files when our stock_id is not present
        if stock_id not in stock_ids:
            logger.debug( "loading image '%s' as stock icon '%s'" % (file, stock_id) )
            pixbuf = gtk.gdk.pixbuf_new_from_file(file)
            pixbuf = pixbuf.scale_simple(48,48,gtk.gdk.INTERP_BILINEAR)
            iconset = gtk.IconSet(pixbuf)
            iconfactory.add(stock_id, iconset)
    iconfactory.add_default()
    

def test_progressbar():
    
    def mygen():
        import time
        for i in range(1,100):
            time.sleep(1)
            yield (i,100,"Step #%d" % i)

    def call_me(sender):
        progress_bar( mygen )

    main = gtk.Window(gtk.WINDOW_TOPLEVEL)
    btn = gtk.Button('click me')
    main.add(btn)
    btn.show(); main.show()
    
    btn.connect('clicked', call_me)
    gtk.main()

def test_register_icons():

    register_all_png_icons('./Icons')
    
    main = gtk.Window(gtk.WINDOW_TOPLEVEL)
#    btn = gtk.Button(label='replot', stock="replot")
#    btn.set_use_stock(True)
    btn = gtk.Image()    
    btn.set_from_stock('replot', gtk.ICON_SIZE_BUTTON)
    main.add(btn)
    btn.show(); main.show()
    gtk.main()
    
if __name__ == "__main__":
    test_register_icons()
    




# DEPRECATED

# def fix_actions(actions,instance):
#     """    
#     Maps methods of an action list for the UIManager to an instance.
#     Taken from pygtk/examples and modified slightly.    
#     """
#     retval = []

#     for i in range(len(actions)):
#         curr = actions[i]
#         if len(curr) > 5:
#             curr = list(curr)
#             # if last field is a string, find the corresponding instance-method 
#             if isinstance(curr[5],basestring):
#                 curr[5] = getattr(instance, curr[5])
#             curr = tuple(curr)
            
#         retval.append(curr)
#     return retval




# def progress_bar(cb_action_generator,cb_arguments=None):
#     # TODO:
#     # TODO: implement cancelling of job.
#     # TODO:
#     """
#     Create a modal window with a progress bar.

#     The passed `cb_action_generator` is a generator function,
#     yielding a tuple (current, max, label). The label below
#     the progress bar is updated with each yield and the
#     fraction of the progress bar is calculated by current/max.

#     If you need to have extra arguments passed to the function,
#     you must wrap them as a tuple.

#     def my_action(args):
#         import time

#         (first,second)=args
#         # do this and that
#         for i in range(100):
#             time.sleep(1)
#             yield(i,100,'step %d' % i)

#     progress_bar(my_action, ('first','second'))
    
#     """
#     window = gtk.Window(gtk.WINDOW_TOPLEVEL)
#     window.set_modal(True)
#     window.set_position(gtk.WIN_POS_CENTER_ALWAYS)

#     vbox = gtk.VBox() ; vbox.show()
#     window.add(vbox)
    
#     pb = gtk.ProgressBar() ; pb.show()
#     pb.set_fraction(0.0)
#     vbox.pack_start(pb)

#     l = gtk.Label() ; l.show()
#     vbox.pack_start(l)

#     window.show()
    
#     while gtk.events_pending():
#         gtk.main_iteration()

#     try:
#         for (current,max,label) in cb_action_generator(cb_arguments):
#             print current,max,label
#             pb.set_fraction(float(current)/max)
#             l.set_label(label)
#             while gtk.events_pending():
#                 gtk.main_iteration()
#     finally:
#         window.destroy()

    
