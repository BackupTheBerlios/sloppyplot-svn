
__all__ = ['Base','Filters','Lib', 'Plugins',
           'ImporterRegistry', 'ExporterRegistry',
           'Cli']

import logging
logger = logging.getLogger()

#
# set correct path to SloppyPlot
#

#import os.path
#from Base import const

#path = os.path.split(Base.__path__[0])[0]
#logger.info("Setting SloppyPath to %s" % path)
#const.set_path(path)



#
# add matplotlib backend ('mpl') if matplotlib is available
#

def init():
    try:
	import Matplot
	__all__.append('Matplot')
    except ImportError:
	logger.warn("matplotlib not found.")
	raise
    
    import Gnuplot

    import Importer
    import Exporter
