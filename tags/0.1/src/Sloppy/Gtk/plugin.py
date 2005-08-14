
import gtk


class ActionWrapper:
    def __init__(self, name, label, tooltip=None, stock_id=None):
        self.action = gtk.Action(name,label,tooltip,stock_id)        
        self.name = name
        
    def connect(self, cb, *args, **kwargs):
        self.action.connect('activate', cb, *args, **kwargs)
