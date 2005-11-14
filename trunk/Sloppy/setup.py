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

# Place to put shared data.
# TODO: This should be adjusted for windows.
PATH_SHARED=join(sys.prefix,'share','sloppyplot')

# Much information is taken from Sloppy.Base.version, as we
# don't want to write down all of it twice!  The next lines
# make sure that we import the variables from the correct
# Sloppy.Base.version.
import os
source_dir = os.path.join(os.path.curdir, 'src')
os.sys.path.insert(0, source_dir)
from Sloppy.Base.version import NAME, VERSION, LONG_DESCRIPTION, URL


setup(name=NAME,
      version=VERSION, 
      description=LONG_DESCRIPTION,
      author='Niklas Volbers',
      author_email = 'mithrandir42@web.de',
      url=URL,
      download_url=URL,
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
		'Sloppy.Plugins.Pygsl',
		'Sloppy.Plugins.PeakFinder',
                'Sloppy.Cli',
                'Sloppy.Gtk',
		'Sloppy.Lib',
                'Sloppy.Lib.ElementTree',
                'Sloppy.Lib.Signals',
                'Sloppy.Lib.Undo',
                'Sloppy.Lib.Props',
		'Sloppy.Lib.Props.Gtk'
                ],
      package_data = {'Sloppy.Gtk' :
                       [join('Data', 'explorer.xml'),
                        join('Icons', '*.png')]},
      # second argument of data_files tuples is a list!
      data_files = [(join(PATH_SHARED,'Examples'),
                     glob(join("Examples","*.spj"))),
		    (join(PATH_SHARED,'Examples','Data'),
		     glob(join("Examples","Data","*.dat"))),
                    (join(sys.prefix,'share','applications'),
		     ['sloppyplot.desktop']),
                    (join(sys.prefix, 'share', 'pixmaps'),
                     [join("src", "Sloppy", "Gtk", "Icons", "sloppyplot.png")])
		     ],
      scripts = [ join('src', 'sloppyplot') ],

      # see http://python.org/pypi?%3Aaction=list_classifiers
      classifiers = ["Development Status :: 3 - Alpha",
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
