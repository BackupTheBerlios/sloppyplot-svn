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
Commonly used helper functions for pygtk.
"""

import gtk

import logging
logger = logging.getLogger('gtk.uihelper')



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


def construct_buttonbox(buttons,
                        horizontal=True,
                        show_stock_labels=True,
                        layout=gtk.BUTTONBOX_END):
    if horizontal is True:
        btnbox = gtk.HButtonBox()
    else:
        btnbox = gtk.VButtonBox()
    btnbox.set_layout(layout)

    for label, stock, callback in buttons:
        if label is not None:
            button = gtk.Button(label)
        else:
            button = gtk.Button(stock=stock)
            if show_stock_labels is False:
                alignment = button.get_children()[0]
                hbox = alignment.get_children()[0]
                image, label = hbox.get_children()
                label.set_text('')                

        button.show()

        button.connect('clicked', callback)
        btnbox.pack_end(button,False,False)

    return btnbox



        
# DEPRECATED?
# def set_actions(uimanager, action_names_list, state=True):
#     for action_name in action_names_list:
#         action = uimanager.get_action(action_name)
#         if action is not None:
#             action.set_property('sensitive', state)
#         else:
#             logger.error("Could not find action %s." % action_name)

# def add_ui(uimanager, actions_dict, uistring, map=None):
#     """
#     Returns a tuple (uimanager, actiongroups, merge_id) that can
#     be passed on to remove_ui like this:

#     >>> ui_info = add_ui(...)
#     >>> remove_ui(*ui_info)    
#     """
#     actiongroups = list()
#     for key, actions in actions_dict.iteritems():
#         actiongroups.append( add_actions(uimanager, key, actions, map) )            

#     merge_id = uimanager.add_ui_from_string(uistring)
#     return (uimanager, actiongroups, merge_id)        


# def remove_ui(uimanager, actiongroups, merge_id):
#     uimanager.remove_ui(merge_id)
#     for ag in actiongroups:
#         uimanager.remove_action_group(ag)
