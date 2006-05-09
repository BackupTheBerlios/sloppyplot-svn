
""" Common base widget for both Plot and Dataset widgets. """

import gtk

import logging
logger = logging.getLogger('Gtk.basewidget')



class BaseWidget(gtk.VBox):

    actions_dict = {'Test': [('TestMenu', None, '_Test')]}
    
    def __init__(self, project):
        gtk.VBox.__init__(self)

        # set project
        self.project = None
        self.project_signal = None
        self.set_project(project)

        # construct action groups (requires actions_dict)
        actiongroups = list()
        for key, actions in self.actions_dict.iteritems():
            ag = gtk.ActionGroup(key)
            ag.add_actions( uihelper.map_actions(actions, self) )
            actiongroups.append(ag)
        self.actiongroups = actiongroups

        # activate/deactivate actiongroup on focus-in/focus-out
        self.connect("focus-in-event", self.on_focus_in_event)
        self.connect("focus-out-event", self.on_focus_out_event)


    def set_project(self, project):
        if self.project != project and self.project_signal is not None:
            project.sig_disconnect(self.project_signal)
            self.project_signal = None
            
        self.project = project
        if self.project is not None:
            self.project_signal = project.sig_connect("close", lambda sender: self.destroy())
        

    def get_actiongroups(self):
        return self.actiongroups

    def get_uistring(self):
        return globals.app.get_uistring('plot-widget')



    def on_focus_in_event(self, event):
        print "FOCUS IN"

    def on_focus_out_event(self, event):
        print "FOCUS OUT"
