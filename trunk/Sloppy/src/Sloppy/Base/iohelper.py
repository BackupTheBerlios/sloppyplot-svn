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

# $HeadURL: svn+ssh://svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Base/application.py $
# $Id: application.py 274 2005-11-16 22:58:53Z niklasv $



from Sloppy.Lib.ElementTree.ElementTree import Element, SubElement



def write(element, key, value):        
    " Set If Valid -- only set element attribute if value is not None. "
    if value is not None:
        element.set(key, unicode(value))

def set_attributes(element, attributes={}):
    for k,v in attributes.iteritems():
        if v is not None:
            element.set(k, unicode(v))


def write_list(element, listname, alist):
    eNode = SubElement(element, listname)
    for item in alist:                
        eItem = SubElement(eNode, 'Item')
        if item is not None:
            eItem.text = unicode(item)

def write_dict(element, dictname, adict):
    eNode = SubElement(element, dictname)
    for key,item in adict.iteritems():
        eItem = SubElement(eNode, 'Item')
        if item is not None:
            eItem.text = unicode(item)
        else:
            eItem.text = None
        eItem.attrib['key'] = unicode(key)

def read_list(element, listname):
    alist = []
    for eItem in element.findall('%s/Item' % listname):
        item = eItem.text
        alist.append(item)
    return alist

def read_dict(element, dictname):
    adict = {}
    for eItem in element.findall('%s/Item' % dictname):
        key = eItem.attrib['key']
        value = eItem.text
        adict[key] = value
    return adict


def beautify_element(element):
    """ Beautify the XML output by inserting some newlines.

    This assumes that the element's tail is never used.
    It also assumes that if the element has children,
    and there is no text, then it is o.k. to append
    a newline to the text.
    """

    children = element.getchildren()
    
    element.tail = '\n'
    if element.text is None and len(children) > 0:
        element.text = '\n'
    for sub_element in children:
        beautify_element(sub_element)
