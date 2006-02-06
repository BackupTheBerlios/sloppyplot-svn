from Sloppy.Lib.Props import HasProperties, Unicode, Dictionary, Boolean
        
class NodeInfo(HasProperties):
    label = Unicode()
    metadata = Dictionary(Unicode)

    # might be used to notify the user that this has been edited,
    # e.g. by displaying a star in a treeview.    
    edit_mark = Boolean()
    

class Node:       
    def __init__(self):
        self.node_info = NodeInfo()
