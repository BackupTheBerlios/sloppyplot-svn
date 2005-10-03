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

# ----------------------------------------------------------------------
#  permitted values
# ----------------------------------------------------------------------

PV = {
#    'PointType': ['circle','square'],
    'legend.position': [None, 'best', 'center', 'lower left', 'center right', 'upper left',
                        'center left', 'upper right', 'lower right',
                        'upper center', 'lower center',
                        'outside', 'at position'],
    'axis.scale': [None, 'linear','log'],
    'axis.key': ['x','y','z'],
    'line.style' : [None,"None","solid","dashed","dash-dot","dotted","steps"],
    'line.marker' : [None,"None","points","pixels","circle symbols",
                   "triangle up symbols",
                   "triangle down symbols",
                   "triangle left symbols",
                   "triangle right symbols",
                   "square symbols",
                   "plus symbols",
                   "cross symbols",
                   "diamond symbols",
                   "thin diamond symbols",
                   "tripod down symbols",
                   "tripod up symbols",
                   "tripod left symbols",
                   "tripod right symbols",
                   "hexagon symbols",
                   "rotated hexagon symbols",
                   "pentagon symbols",
                   "vertical line symbols",
                   "horizontal line symbols"
                   "steps"],
    'layer.type' : ['line2d', 'contour']
    }

# Note that entries marked with '#' have a similar
# entry in PV and will contain PV[key][0].
default_params = {
    'project.label'  : u'Unnamed Project',
    'project.comment': None,
    'plot.title'     : None,
    'plot.comment'   : None,
    'axis.label'     : None,
    'axis.scale'     : None, #
    'axis.start'     : None,
    'axis.end'       : None,
    'axis.key'       : None, #
    'axis.format'    : None,
    'legend.label'   : None,
    'legend.position': None, #
    'legend.visible' : True,
    'legend.border'  : False,
    'legend.x'       : 0.7,
    'legend.y'       : 0.0,
    'line.label'     : u'<unnamed>',
    'line.visible'   : True,
    'line.info'      : None,
    'line.style'     : 'solid', #
    'line.marker'    : 'None', #
    'line.color'     : 'g',
    'line.source'    : None,
    'line.width'     : 1,            ###
    'line.cx'        : 1,
    'line.cy'        : 2,
    'line.cxerr'     : None,
    'line.cyerr'     : None,
    'layer.type'     : None, #
    'layer.grid'     : False,
    'layer.title'    : None,
    'layer.x'        : 0.11,
    'layer.y'        : 0.125,
    'layer.width'    : 0.775,
    'layer.height'   : 0.79,
    'layer.visible'  : True,
    'layer.group_colors' : 'bgrcmyk',  ###
    'layer.group_styles' : ['solid', 'dashed'],
    'layer.group_markers' : ['points'],
    'dataset.label'  : None
    }

DP = default_params # shortcut


def replace_default_parameters():
    """    
    This function looks for keys in default_params, that have a
    pendant in the dict PV of possible values.  If there is such a
    list available, and if there is no default parameter given (None),
    the first entry is used as the default value.
    """
    for (k,v) in PV.iteritems():
        if k in default_params and v is None:
            default_params[k] = v[0]

replace_default_parameters()

#------------------------------------------------------------------------------
