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



from Sloppy.Base.dataset import Dataset
from Sloppy.Base.project import Project
from Sloppy.Base import utils
from Sloppy.Base.objects import Legend, Axis, Plot, Layer, Line, TextLabel
from Sloppy.Base.error import NoData
from Sloppy.Base import pdict
from Sloppy.Base.dataio import ExporterRegistry, read_table_from_stream
from Sloppy.Base.table import Table, Column

from Sloppy.Lib.ElementTree.ElementTree import ElementTree, Element, SubElement, parse

import tarfile
import tempfile
import os
import shutil

from Numeric import *

#------------------------------------------------------------------------------
import logging
logger = logging.getLogger('Base.projectio')


DEFAULT_FF = "SIF"
FILEFORMAT = "0.4.3"

"""
File format history:
  - 0.3 -> 0.4: Table.cols -> Table.ncols  (transformation implemented)
  - 0.4 -> 0.4.3: added layer.labels (no conversion required)
"""

class ParseError(Exception):
    pass



def dataset_filename(key):
    """  The filename is dynamically created from the given key,
    appended by the extension '.nc'. """
    #TODO: escape special characters, like '/'
    if not isinstance(key, basestring):
        raise TypeError("construct_filename: 'key' must be a valid string, but it is of %s" % type(key))
    return "%s.nc" % key



#------------------------------------------------------------------------------
# Object Creation (starting with new_xxx)


def new_dataset(spj, element):
    ncols = int(element.attrib.pop('ncols',0))
    typecodes = element.attrib.pop('typecodes','')
    
    ds = Dataset(**element.attrib)

    # metadata
    for eMetaitem in element.findall('Metadata/Metaitem'):
        key = eMetaitem.attrib['key']
        value = eMetaitem.text
        ds.metadata[key] = unicode(value)

    # actual Table
    if element.tag == 'Table':

        # Extract additional column information.
        # This information will be passed on to 'set_table_import',
        # which will pass it on to the internal importer.        
        column_props = list()
        for i in range(ncols):
            column_props.append(dict())
        
        for eColumn in element.findall('Column'):
            n = int(eColumn.get('n'))
            p = column_props[n]
            for eInfo in eColumn.findall('Info'):
                key = eInfo.get('key', None)
                if key is not None:
                    p[key] = unicode(eInfo.text)

        filename = os.path.join('datasets', dataset_filename(ds.key))
        # TODO: replace DEFAULT_FF with read value
        ds.set_table_import(spj, filename, typecodes, column_props, DEFAULT_FF)
    
    return ds


def new_label(spj, element):
    text = element.text
    element.attrib['text'] = text
    label = TextLabel(**element.attrib)
    return label

def new_line(spj, element):
    source = element.attrib.get('source', None)
    try:
        element.attrib['source'] = spj.get_dataset(source)
    except KeyError:
        logger.warn("Dataset %s not found" % source)
        element.attrib['source'] = None

    line = Line(**element.attrib)
    return line


def new_legend(spj, element):
    legend = Legend(**element.attrib)
    return legend
    

def new_layer(spj, element):
    layer = Layer(**element.attrib)

    # TODO: test type and _then_ assign the data    
    for eLine in element.findall('Line'):        
        layer.lines.append(new_line(spj, eLine))        

    # TODO:
    ### group properties
    ###group_markers = element.findall('GroupMarkers')
    
    
    for eAxis in element.findall('Axis'):
        key = eAxis.attrib.pop('key', 'x')
        a = Axis(**eAxis.attrib)
        if key == 'x':
            layer.xaxis = a
        elif key == 'y':
            layer.yaxis = a

    eLegend = element.find('Legend')
    if eLegend is not None:
        layer.legend = new_legend(spj, eLegend)
    
    return layer
    
    
def new_plot(spj, element):
    plot = Plot(**element.attrib)

    for eLayer in element.findall('Layers/Layer'):
        layer = new_layer(spj, eLayer)
        plot.layers.append(layer)

        for eLabel in eLayer.findall('Labels/Label'):
            layer.labels.append(new_label(spj, eLabel))
        
    eComment = element.find('comment')
    if eComment is not None:
        plot.comment = unicode(eComment.text)
        
    return plot



def fromTree(tree):
    eProject = tree.getroot()
                    
    spj = Project()

    version = eProject.get('version', None)
    def raise_version(new_version):
        logger.info("Converted SloppyPlot Archive to version %s" % new_version)
        return new_version
    
    while (version is not None and version != FILEFORMAT):
        if version=='0.3':
            eTables = tree.findall('Datasets/Table')
            for eTable in eTables:
                ncols = eTable.get('cols',None)
                if ncols is not None:
                    eTable.set('ncols',str(ncols))

            version = raise_version('0.4')
            continue
        #
        elif version=='0.4':
            version = raise_version('0.4.3')
            continue
        #
        else:
            raise IOError("Invalid Sloppy File Format Version %s. Aborting Import." % version)        

    for eDataset in eProject.findall('Datasets/*'):
        spj.datasets.append( new_dataset(spj, eDataset))

    for ePlot in eProject.findall('Plots/*'):
        spj.plots.append( new_plot(spj, ePlot) )
    
    return spj



#------------------------------------------------------------------------------
# Writing objects to ElementTree Elements


def toElement(project):

    # helper function
    def safe_set(element, key, value):
        if value is not None: # and isinstance(value, basestring):
            element.set(key, str(value))    

    eProject = Element("Project")
    eProject.attrib['version'] = FILEFORMAT

    eDatasets = SubElement(eProject, "Datasets")
    for ds in project.datasets:
        if ds.get_data() is None:
            raise RuntimeError("EMPTY DATASET '%s'" % ds.key)
        
        if isinstance(ds.data, Table):
            tbl = ds.data
            
            eData = SubElement(eDatasets, 'Table')            
            safe_set(eData, 'ncols', tbl.ncols)
            safe_set(eData, 'typecodes', tbl.typecodes_as_string)

            # We write all Column properties except for the
            # key and the data to the element tree, because
            # netCDF does not like unicode!
            n = 0
            for column in tbl.get_columns():
                kw = column.get_values(exclude=['key','data'])
                if len(kw) > 0:
                    eColumn = SubElement(eData, 'Column')
                    safe_set(eColumn, 'n', n)
                    for k,v in kw.iteritems():
                        if v is not None:
                            eInfo = SubElement(eColumn, 'Info')
                            safe_set(eInfo, 'key', k)
                            eInfo.text = v
                n += 1
                
            
        elif isinstance(ds.data, ArrayType): # TODO: untested
            eData = SubElement(eDatasets, 'Array')
        else:
            raise RuntimeError("Invalid dataset", ds)
        
        safe_set(eData, 'key', ds.key)

        if len(ds.metadata) > 0:
            eMetadata = SubElement(eData, "Metadata")
            for k,v in ds.metadata.iteritems():
                eMetaitem = SubElement(eMetadata, 'Metaitem')
                eMetaitem.set('key', k)
                eMetaitem.text = str(v)
                       
    ePlots = SubElement(eProject, "Plots")
    for plot in project.plots:
        ePlot = SubElement(ePlots, plot.__class__.__name__)
        safe_set(ePlot, 'key', plot.key)
        safe_set(ePlot, 'title', plot.title)

        if hasattr(plot, "comment"):
            eComment = SubElement(ePlot, "comment")
            eComment.text = plot.comment

        eLayers = SubElement(ePlot, "Layers")
        for layer in plot.layers:
            
            eLayer = SubElement(eLayers, "Layer")
            safe_set(eLayer, 'type', layer.type)
            safe_set(eLayer, 'grid', layer.grid)
            safe_set(eLayer, 'title', layer.title)
            safe_set(eLayer, 'visible', layer.visible)
            
                
            for (key, axis) in layer.axes.iteritems():
                eAxis = SubElement(eLayer, "Axis")
                eAxis.set('key', key)
                safe_set(eAxis, 'label', axis.label)
                safe_set(eAxis, 'scale', axis.scale)
                safe_set(eAxis, 'start', axis.start)
                safe_set(eAxis, 'end', axis.end)

                safe_set(eAxis, 'format', axis.format)

            legend = layer.legend
            if legend is not None:
                eLegend = SubElement(eLayer, "Legend")
                safe_set(eLegend, 'label', legend.label)
                safe_set(eLegend, 'position', legend.position)
                safe_set(eLegend, 'visible', legend.visible)
                safe_set(eLegend, 'border', legend.border)
                safe_set(eLegend, 'x', legend.x)
                safe_set(eLegend, 'y', legend.y)
                                     
            for line in layer.lines:
                eLine = SubElement(eLayer, "Line")

                safe_set(eLine, 'label', line.label)
                safe_set(eLine, 'style', line.style)
                safe_set(eLine, 'type', line.marker)
                safe_set(eLine, 'visible', line.visible)

                # For the line source we must check first
                # if this is not a temporary source.
                # TODO: if it was a temporary source we either
                # need to ignore the source (current situation)
                # or add the temporary dataset to the project.
                if line.source is not None:
                    if project.has_dataset(key=line.source.key):
                        safe_set(eLine, 'source', line.source.key)
                    else:
                        logger.warn("Invalid line source. Skipped source.")
                
                safe_set(eLine, 'width', line.width)                

                safe_set(eLine, 'cx', line.cx)
                safe_set(eLine, 'cy', line.cy)
                safe_set(eLine, 'row_first', line.row_first)
                safe_set(eLine, 'row_last', line.row_last)
                #safe_set(eLine, 'value_range', line.value_range)
                
                safe_set(eLine, 'cxerr', line.cxerr)                
                safe_set(eLine, 'cyerr', line.cyerr)

            # layer.labels
            if len(layer.labels) > 0:
                eLabels = SubElement(eLayer, "Labels")
                for label in layer.labels:
                    eLabel = SubElement(eLabels, "Label")
                    safe_set(eLabel, 'x', label.x)
                    safe_set(eLabel, 'y', label.y)
                    safe_set(eLabel, 'system', label.system)
                    safe_set(eLabel, 'valign', label.valign)
                    safe_set(eLabel, 'halign', label.halign)
                    eLabel.text = label.text                              

    # beautify the XML output by inserting some newlines
    def insert_newlines(element):
        element.tail = '\n'
        if element.text is None:
            element.text = "\n"
        for sub_element in element.getchildren():
            insert_newlines(sub_element)
    insert_newlines(eProject)
        
    return eProject



def save_project(spj, filename=None, path=None):
    """
    Write the whole project to a file.  Return True on success.
    
    The archive that is created is a gzipped tar file containing
    the XML file with the project info and additionally the data
    files containing the information from the current Dataset
    objects.
    """

    #
    # write project XML file
    #

    tempdir = tempfile.mkdtemp(prefix="spj-export-")
    filename = filename or spj.filename
    if filename is None:
        raise RuntimeError("No valid filename specified.")                                              

    try:
        projectfile = os.path.join( tempdir,'project.xml' )
        e = toElement(spj)

        fd = open(projectfile, 'w')
        fd.write('<?xml version="1.0" encoding="utf-8"?>\n')
        ElementTree(e).write(fd, encoding="utf-8")
        fd.close()

        #
        # now add all extra information to the tempdir
        # (Datasets and other files)
        #

        # add Dataset files to tempdir
        exporter = ExporterRegistry[DEFAULT_FF]()

        dsdir = os.path.join(tempdir, 'datasets')
        os.mkdir(dsdir)
        for ds in spj.datasets:
            try:
                dspath = os.path.join(dsdir, dataset_filename(ds.key))
                exporter.write_to_file(dspath, ds.data)
            except AttributeError:
                logger.error("Error while writing Dataset '%s'" % ds.key)
                raise
            except NoData:
                logger.error("Warning, empty Dataset -- no data file written.")


        #
        # create tar archive from tempdir
        #
        try:
            archive = None
            try:
                if path is not None:
                    filename = os.path.join(path, os.path.basename(filename))
                logger.info("Writing archive '%s'" % filename)
                archive = tarfile.open(filename, mode="w:gz")
                archive.add( tempdir, '' )
            except IOError,(nr, msg):
                logger.error('Error while creating archive "%s": %s' % (filename, msg))
                return False

        finally:
            if archive is not None:
                archive.close()
    finally:
        logger.debug("Removing directory %s" % tempdir)
        shutil.rmtree(tempdir)
        
    logger.debug("Finished writing '%s'" % filename)
    return True




def load_project(filename):
    """
    Helper function that creates a whole new project from
    the given project file (extension spj).
    
    >>> load_project("zno.spj")
    """
    
    try:
        archive = tarfile.open(filename,'r:gz')
    except tarfile.ReadError:
        logger.error('Error while opening archive "%s"' % filename)
        raise FileNotFoundError

    logger.debug("Creating project from project.xml")
        
    # Create Project from file
    try:
        projectfile = archive.extractfile("project.xml")
        project = fromTree( parse(projectfile) )
        project.filename = filename
    except:
        raise

    # remember the archive so that it can be closed later on
    project._archive = archive

    return project  
