# This file is part of SloppyPlot, a scientific plotting tool.
# Copyright (C) 2005 Niklas Volbers
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# $HeadURL$
# $Id$


"""
Constant declarations.
"""


import logging
logger = logging.getLogger('Base.const')

import os

#
# path handling
#
the_path = []
def set_path(path):
    global the_path
    the_path.append(path)
def internal_path(*path):
    global the_path
    if len(the_path) == 0:
	logger.error("Fatal Error: internal path not set up properly!")
	raise SystemExit
    return os.path.join( the_path[-1], *path )


PATH_EXAMPLE  = os.path.join('../../Examples')
PATH_DATA     = os.path.join('Base','Data')
PATH_ICONS    = os.path.join('Gtk','Icons')

# determine config path
if os.environ.has_key('XDG_CONFIG_HOME'):
    PATH_CONFIG = os.path.expandvars('${XDG_CONFIG_HOME}/SloppyPlot')
else:
    PATH_CONFIG = os.path.expanduser('~/.config/SloppyPlot')

CONFIG_FILE = os.path.join(PATH_CONFIG, 'config.xml')


# TODO: how to represent absolut dirs?
LOGFILE = os.path.join('/','var','tmp','sloppyplot.log')

DEBUG_SIGNALS = False
DEBUG_FILTERS = False

#DEFAULT_BACKEND = 'gnuplot/x11'
DEFAULT_BACKEND = 'matplotlib'

