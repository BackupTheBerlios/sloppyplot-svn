"""
   A complete re-implementation of the Backend mechanism.

   @copyright: 2006, Niklas Volbers <mithrandir42@web.de>
"""


import gtk

from Sloppy.Base.objects import SPObject
from Sloppy.Base import objects
from Sloppy.Lib.Check import Instance, List, Dict, Check


import logging
logger = logging.getLogger('Backends.mpl3')
#------------------------------------------------------------------------------

class Artist(SPObject):
    """ Any class that renders some information as graphic is an Artist.

    Currently, I am assuming a 1:1 mapping of data objects and Artist objects.
    The corresponding object is thus accessible via self.
    """

    parent = Check()
    obj = Check()
    artists = Dict()

    def __init__(self, **kwargs):
        SPObject.__init__(self, **kwargs)
        self.init()
        

# Any Artist class starts with A, so that they can easily be distinguished
# from the data objects.

class APlot(Artist):

    obj = Instance(objects.Plot)
    
    def init(self):
        pass
        
        
    


ap = APlot()
