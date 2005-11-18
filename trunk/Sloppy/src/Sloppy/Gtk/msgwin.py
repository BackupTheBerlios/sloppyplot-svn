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

# $HeadURL: svn+ssh://svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Gtk/uihelper.py $
# $Id: uihelper.py 187 2005-10-10 04:45:37Z niklasv $



import gtk

import logging
logger = logging.getLogger('gtk.uihelper')


"""

Brainstorming, or 'How is this going to work?':

msgwin shoudl provide the following:

- display an error dialog whenever an exception occurs _EXCEPT_ for
  the case, that we have a UserAbort

- display an error (where?) whenever an error message is logged.




"""
