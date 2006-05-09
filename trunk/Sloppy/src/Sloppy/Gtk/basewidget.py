
""" Common base widget for both Plot and Dataset widgets. """

import gtk

import logging
logger = logging.getLogger('Gtk.basewidget')

from Sloppy.Gtk import uihelper
from Sloppy.Base import globals


class BaseWidget(gtk.VBox):

    """ BaseWidget

    Derived classes need to define

    - actions_dict
    -

    The following attributes are set:

    - project
    - project_signal
    - actiongroups

    The following methods may be overwritten:

    - activate
    - deactivate
    - get_actiongroups
    - get_uistring
    - get_statusbar
    - get_uimanager

    """

    
    actions_dict = {'Test': [('TestMenu', None, '_Test')]}
    
    def __init__(self, project):
        gtk.VBox.__init__(self)

        # set project
        self.project = None
        self.project_signal = None
        self.set_project(project)

        # keep track of registered items
        self._registered = {'group':[], 'ui':[]}
        self._parent = None


    def set_project(self, project):
        if self.project != project and self.project_signal is not None:
            project.sig_disconnect(self.project_signal)
            self.project_signal = None
            
        self.project = project
        if self.project is not None:
            self.project_signal = project.sig_connect("close", lambda sender: self.destroy())

        

    def get_actiongroups(self):
        """ Return actiongroups to be registered. """
        if not hasattr(self, 'actiongroups') or self.actiongroups is None:
            # construct action groups (requires actions_dict)
            actiongroups = list()
            for key, actions in self.actions_dict.iteritems():
                ag = gtk.ActionGroup(key)
                ag.add_actions( uihelper.map_actions(actions, self) )
                actiongroups.append(ag)
            self.actiongroups = actiongroups            
        return self.actiongroups

    def get_uistring(self):
        return ''

    def get_statusbar(self):
        return globals.app.window.statusbar

    def get_uimanager(self):
        return globals.app.window.uimanager
    


    def activate(self):
        uimanager = self.get_uimanager()

        for ag in self.get_actiongroups():
            uimanager.insert_action_group(ag, 0)
            self._registered['group'].append(ag)
            
        ##self.get_container().add_accel_group(uimanager.get_accel_group())
        merge_id = uimanager.add_ui_from_string(self.get_uistring())
        self._registered['ui'].append(merge_id)
        

    def deactivate(self):
        uimanager = self.get_uimanager()

        for group in self._registered['group']:
            uimanager.remove_action_group(group)
        self._registered['group'] = []

        for ui in self._registered['ui']:
            uimanager.remove_ui(ui)
        self._registered['ui'] = []        


    #----------------------------------------------------------------------

    # TODO: since the label might change anytime, it would be best
    # to implement it as a real property

    def get_title(self):
        return "BASEWIDGET"
