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
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# $HeadURL: svn+ssh://niklasv@svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Plugins/Default/__init__.py $
# $Id: __init__.py 487 2006-02-09 21:16:41Z niklasv $


"""
Commonly used functions.
"""


from Sloppy.Base.version import VERSION

name = "core"  # DO NOT CHANGE THIS OR SLOPPYPLOT WILL NOT START!
authors = "Niklas Volbers"
license = "GPLv2"
blurb = "Core functions for SloppyPlot"
version = VERSION


from import_export import *
from functions import *

