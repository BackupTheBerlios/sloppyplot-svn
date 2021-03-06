
__all__ = ['Base','Filters','Lib', 'Plugins',
           'ImporterRegistry', 'ExporterRegistry',
           'Application', 'Cli']

import logging
logger = logging.getLogger()

#
# add matplotlib backend ('mpl') if matplotlib is available
#
try:
    import Matplot
    __all__.append('Matplot')
except ImportError:
    logger.warn("matplotlib not found.")
    raise
import Gnuplot

import Importer
import Exporter
from application import Application
