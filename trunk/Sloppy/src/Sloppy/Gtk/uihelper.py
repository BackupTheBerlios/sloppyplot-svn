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
Commonly used helper functions and classes for pygtk.
"""

import gtk

import logging
logger = logging.getLogger('gtk.uihelper')

import urllib
import glob, os

SECTION_SPACING=8


def get_file_path_from_dnd_dropped_uri(uri):
    # thanks to the pygtk FAQ entry 23.31
    path = urllib.url2pathname(uri).strip('\r\n\x00')

    # get the path to file
    if path.startswith('file:\\\\\\'): # windows
            path = path[8:] # 8 is len('file:///')
    elif path.startswith('file://'): # nautilus, rox
            path = path[7:] # 7 is len('file://')
    elif path.startswith('file:'): # xffm
            path = path[5:] # 5 is len('file:')

    return path


def add_actions(uimanager, key, actions, map=None):
    if map is not None:
        actions = map_actions(actions, map)

    actiongroup = gtk.ActionGroup(key)
    actiongroup.add_actions(actions)
    uimanager.insert_action_group(actiongroup, 0)
    return actiongroup


def add_toggle_actions(uimanager, key, actions, map=None):
    if map is not None:
        actions = map_actions(actions, map)

    actiongroup = gtk.ActionGroup(key)
    actiongroup.add_toggle_actions(actions)
    uimanager.insert_action_group(actiongroup, 0)
    return actiongroup


def map_actions(actions, map):
    """    
    Maps methods of an action list for the UIManager to instance `map`.
    Taken from pygtk/examples and modified slightly.    
    """
    retval = []

    for action in actions:            
        if len(action) > 5:
            curr = list(action)
            # if last field is a string, find the corresponding instance-method 
            if isinstance(curr[5],basestring):
                curr[5] = getattr(map, curr[5])
            curr = tuple(curr)
        else:
            curr = action                
        retval.append(curr)

    return retval



def get_action_group(uimanager, key):
    actiongroups = uimanager.get_action_groups()
    keylist = [ag for ag in actiongroups if ag.get_name() == key]
    if len(keylist) > 0:
        return keylist[-1]
    else:
        return None   



def add_scrollbars(widget, viewport=False, show=True):
    " Returns a scrollbar window that wraps the given widget. "
    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    if viewport is True:
        print "Adding with viewport"
        sw.add_with_viewport(widget)
    else:
        sw.add(widget)
    if show is True:
        sw.show()
    return sw


def construct_actiongroups(actions_dict, map):
    actiongroups = list()
    for key, actions in actions_dict.iteritems():
        ag = gtk.ActionGroup(key)
        ag.add_actions( map_actions(actions, map) )
        actiongroups.append(ag)
    return actiongroups



def setup_test_window(widget):
    win = gtk.Window()
    win.connect("destroy", gtk.main_quit)
    win.add(widget)
    widget.show()
    win.show()
    return win


def construct_buttonbox(buttons, horizontal=True, labels=True,
                        layout=gtk.BUTTONBOX_END):
    """
    Construct either a horizontal or a vertical button box.
    The buttons contained are defined in the list 'buttons',
    which is a list with 3-tuples of the form (stock_id, callback).
    If a tuple contains additional items, then these are passed on
    as arguments to the button's connection.
    """
    
    if horizontal is True:
        btnbox = gtk.HButtonBox()
    else:
        btnbox = gtk.VButtonBox()
    btnbox.set_layout(layout)

    for item in buttons:
        stock, callback = item[0:2]
        if len(item) > 2:
            args = item[2:]
        else:
            args = []
            
        button = gtk.Button(stock=stock)
        if labels is False:
            alignment = button.get_children()[0]
            hbox = alignment.get_children()[0]
            image, label = hbox.get_children()
            label.set_text('')                

        button.show()

        if callback is not None:
            button.connect('clicked', callback, *args)
        btnbox.pack_end(button,False,False)

    global SECTION_SPACING
    btnbox.set_spacing(SECTION_SPACING)
#    btnbox.set_border_width(SECTION_SPACING)

    return btnbox


def construct_hbuttonbox(buttons, labels=True, layout=gtk.BUTTONBOX_END):
    return construct_buttonbox(buttons, horizontal=True,
                               labels=labels, layout=layout)

def construct_vbuttonbox(buttons, labels=True, layout=gtk.BUTTONBOX_START):
    return construct_buttonbox(buttons, horizontal=False,
                               labels=labels, layout=layout)


def new_section(frame_title, child):
    """ Surround the given `child` widget by a frame with a given
    title.  The frame itself contains an alignment which causes an
    indentation on the left.  The alignment then contains the child.
    Returns the constructed frame.  """
    
    label = gtk.Label("<b>%s</b>" % frame_title)
    label.set_use_markup(True)

    frame = gtk.Frame()
    frame.set_label_widget(label)
    frame.set_label_align(0.0, 0.5)
    frame.set_shadow_type(gtk.SHADOW_NONE)
    frame.set_border_width(SECTION_SPACING)

    alignment = gtk.Alignment()
    alignment.set(0.15,0.0,1.0,1.0)
    alignment.set_border_width(SECTION_SPACING)
#    alignment.set_padding(0,0,int(1.5*SECTION_SPACING),0)
    alignment.add(child)

    frame.add(alignment)

    return frame


def register_stock_icons(imgdir, prefix=""):
    logger.debug("Trying to register png icons from dir '%s'" % imgdir)
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


def get_active_combobox_item(widget, column_index=0):
    index = widget.get_active()
    if index == -1:                
        return None
    else:
        model = widget.get_model()
        iter = model.get_iter((index,))
        return model.get_value(iter, column_index)
