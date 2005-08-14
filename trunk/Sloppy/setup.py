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

# $HeadURL$
# $Id$



# TODO: for the final distributable version, make sure that

# (1) we use os.path.join for constructing pathes
# (2) that all files contain the appropriate header (license, author, ...)

 
from distutils.core import setup
from os.path import join
from glob import glob
import sys


PATH_SHARED=join(sys.prefix,'share','sloppyplot')
 
SVN_REVISION="SVN"+"$Rev$"[6:-2]



DESCRIPTION="""\
A scientific plotting tool that currently only supports 2d plots.  The
plots and their data are stored in a single file, keeping the
scientific workspace a little more uncluttered.  A postscript export
using gnuplot is available.
"""

setup(name='sloppyplot',
      version='0.1.%s' % SVN_REVISION,
      description=DESCRIPTION,
      author='Niklas Volbers',
      author_email = 'mithrandir42@web.de',
      url='http://sloppyplot.berlios.de',
      download_url='http://sloppyplot.berlios.de',
      license='GPL',
      package_dir = {'' : 'src'}, 
      packages=['Sloppy',
                'Sloppy.Base',
                'Sloppy.Matplot',
                'Sloppy.Gnuplot',
                'Sloppy.Importer',
                'Sloppy.Exporter',
                'Sloppy.Plugins',
                'Sloppy.Plugins.Sims',
                'Sloppy.Plugins.Default',                
                'Sloppy.Cli',
                'Sloppy.Gtk',
		'Sloppy.Gtk.Plugins',
		'Sloppy.Lib',
                'Sloppy.Lib.ElementTree',
                'Sloppy.Lib.Signals',
                'Sloppy.Lib.Undo',
                'Sloppy.Lib.Props'
                ],
      package_data = {'Sloppy.Gtk' :
                       [join('Data', 'explorer.xml'),
                        join('Icons', '*.png')]},
      # second argument of data_files tuples is a list!
      data_files = [(join(PATH_SHARED,'Examples'),
                     glob(join("src","Sloppy","Examples","*.spj"))),
                    (join(sys.prefix,'share','applications'),
		     ['sloppyplot.desktop']),
                    (join(sys.prefix, 'share', 'pixmaps'),
                     [join("src", "Sloppy", "Gtk", "Icons", "sloppyplot.png")])
		     ],
      scripts = [ join('src', 'sloppy-gtk') ],

      # see http://python.org/pypi?%3Aaction=list_classifiers
      classifiers = ["Development Status :: 2 - Pre-Alpha",
                     #Development Status :: 3 - Alpha
                     #Development Status :: 4 - Beta
                     "Topic :: Scientific/Engineering :: Visualization",
                     "Intended Audience :: Science/Research",
                     "Environment :: X11 Applications :: GTK",
                     "Environment :: Console",                     
                     "Natural Language :: English",
		     "Operating System :: Unix",
                     #"Operating System :: OS Independent",
                     "Programming Language :: Python",
                     "License :: OSI Approved :: GNU General Public License (GPL)"
                     ]    
      )
