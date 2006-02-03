from Sloppy.Lib.Props import HasProperties, Unicode, Dictionary
        
class NodeInfo(HasProperties):
    label = Unicode()
    metadata = Dictionary(Unicode)

class Node:       
    def __init__(self):
        self.node_info = NodeInfo()
