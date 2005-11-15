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

class PathHandler:
    def __init__(self): self.p = {}
    def set(self, k,v): self.p[k] = v
    def bset(self, k,v): self.p[k] = os.path.join(self.p['base'], v)
    def get(self, k): return self.p[k]

def set_path(internal_path):
    global path
    path = PathHandler()
    path.set('base', internal_path)
    path.set('example', os.path.join(os.path.sep, 'usr', 'share', 'sloppyplot', 'Examples'))
    path.bset('data', os.path.join('Base','Data'))
    path.bset('icons',  os.path.join('Gtk','Icons'))
    




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

