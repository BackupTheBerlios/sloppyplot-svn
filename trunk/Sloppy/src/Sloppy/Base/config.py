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


"""
I/O for config file.
"""


from Sloppy.Lib.ElementTree.ElementTree import ElementTree, Element, SubElement, parse
import sys



CONFIG_FILE_VERSION = "0.4.3"

ConfigBuilder = {}

def build_all(app):
    eConfig = Element("Config")
    eConfig.attrib['version'] = CONFIG_FILE_VERSION
    
    for builder in ConfigBuilder.itervalues():
        element = builder(app)
        if element is not None:
            eConfig.append(element)

    # beautify the XML output by inserting some newlines
    def insert_newlines(element):
        element.tail = '\n'
        if element.text is None:
            element.text = "\n"
        for sub_element in element.getchildren():
            insert_newlines(sub_element)
    insert_newlines(eConfig)

    ElementTree(eConfig).write(sys.stdout, encoding="utf-8")    
    
        
