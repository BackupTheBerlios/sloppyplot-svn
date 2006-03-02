from Sloppy.Lib.Check import *
        
class NodeInfo(HasChecks):
    label = Unicode()
    metadata = Dict(Unicode)

    

class Node:       
    def __init__(self):
        self.node_info = NodeInfo()
