
from Sloppy.Base.plugin import PluginRegistry


import pygsl
pygsl.import_all()

class Plugin:        
    def __init__(self, app):
        self.app = app

        
PluginRegistry["pygsl"] = Plugin
