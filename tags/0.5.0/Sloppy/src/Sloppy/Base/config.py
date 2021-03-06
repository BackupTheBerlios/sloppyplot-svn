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

import sys, os

import logging
logger = logging.getLogger('Base.config')


CONFIG_FILE_VERSION = "0.4.3"


def check_path(path):
    """ Make sure path to config file exists. """
    if os.path.exists(path) is False:
        try:
            os.mkdir(path)
        except IOError, msg:
            logging.error("Big Fat Warning: Could not create config path! Configuration will not be saved! Please check permissions for creating '%s'. (%s)" % (PATH_CONFIG, msg))
                
        
def read_configfile(app, filename):
    check_path(os.path.split(filename)[0])

    # open config file
    filename = os.path.expanduser(filename)
    if os.path.isfile(filename) is not True:
        logger.info("No configuration file '%s' found." % filename)
        # create root element
        return Element("Config")
    else:
        logger.info("Reading configuration file '%s'." % filename)
        fd = open(filename, 'r')

    try:
        try:
            eRoot = parse(fd).getroot()
            #parse_all(app, eRoot)
            return eRoot
        except:
            raise
            print "Parse Error"
    finally:
        fd.close()

    


def write_configfile(eConfig, filename):
    check_path(os.path.split(filename)[0])

    filename = os.path.expanduser(filename)
    fd = open(filename, 'w')

    # beautify the XML output by inserting some newlines
    def insert_newlines(element):
        element.tail = '\n'
        if element.text is None:
            element.text = "\n"
        for sub_element in element.getchildren():
            insert_newlines(sub_element)
    insert_newlines(eConfig)
    
    try:
        ElementTree(eConfig).write(fd, encoding="utf-8")
    finally:
        fd.close()
    
