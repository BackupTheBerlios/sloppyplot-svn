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

from Numeric import ArrayType


#------------------------------------------------------------------------------
import logging
logger = logging.getLogger('Base.projectio')


FILEFORMAT = "0.5"

"""
File format history:

  - 0.3 -> 0.4: Table.cols -> Table.ncols  (transformation implemented)

  - 0.4 -> 0.4.3: added layer.labels (no conversion required)

  - 0.4.5 -> 0.5: changed internal file format to netCDF.
    This is an incompatible change, so I decided to drop the
    prior conversions for 0.4.6. Sorry, but this is what Alpha
    software really means.
    
"""

class ParseError(Exception):
    pass



def dataset_filename_ascii(key):
    """  The filename is dynamically created from the given key,
    appended by the extension '.dat'. """
    #TODO: escape special characters, like '/'
    if not isinstance(key, basestring):
        raise TypeError("construct_filename: 'key' must be a valid string, but it is of %s" % type(key))
    return "%s.dat" % key


#------------------------------------------------------------------------------
# Object Creation (starting with new_xxx)


def new_dataset(spj, element):
    ncols = int(element.attrib.pop('ncols',0))
    typecodes = element.attrib.pop('typecodes','')

    # TODO: pass fileformat_version to importer (somehow)
    # TODO: how?
    fileformat = element.attrib.pop('fileformat', 'internal')
    fileformat_version = element.attrib.pop('fileformat_version', None)
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
        
        filename = os.path.join('datasets', dataset_filename_ascii(ds.key))
        ds.set_table_import(spj, filename, typecodes, column_props, fileformat)
        
    
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
        #elif version=='0.4':
        #    version = raise_version('0.4.3')
        #    continue
        #
        #if version=='0.4.3':
        #    version = raise_version('0.4.6')
        #    continue
        #else:
        raise IOError("Invalid Sloppy File Format Version %s. Aborting Import." % version)

    for eDataset in eProject.findall('Datasets/*'):
        spj.datasets.append( new_dataset(spj, eDataset))

    for ePlot in eProject.findall('Plots/*'):
        spj.plots.append( new_plot(spj, ePlot) )
    
    return spj



#------------------------------------------------------------------------------
# Writing objects to ElementTree Elements


def toElement(project):

    def SIV(element, key, value):        
        " Set If Valid -- only set element attribute if value is not None. "
        if value is not None:
            #print " KEY: %s => %s" % (key, str(value))
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
            SIV(eData, 'ncols', tbl.ncols)
            SIV(eData, 'typecodes', tbl.typecodes_as_string)

            # We write all Column properties except for the
            # key and the data to the element tree, because
            # netCDF does not like unicode!
            n = 0
            for column in tbl.get_columns():
                kw = column.get_values(exclude=['key','data'])
                if len(kw) > 0:
                    eColumn = SubElement(eData, 'Column')
                    SIV(eColumn, 'n', n)
                    for k,v in kw.iteritems():
                        if v is not None:
                            eInfo = SubElement(eColumn, 'Info')
                            SIV(eInfo, 'key', k)
                            eInfo.text = v
                n += 1
                
            
        elif isinstance(ds.data, ArrayType): # TODO: untested
            eData = SubElement(eDatasets, 'Array')
        else:
            raise RuntimeError("Invalid dataset", ds)
        
        SIV(eData, 'key', ds.rget('key'))
        SIV(eData, 'fileformat', 'internal-%s' % FILEFORMAT )
        
        if len(ds.metadata) > 0:
            eMetadata = SubElement(eData, "Metadata")
            for k,v in ds.metadata.iteritems():
                eMetaitem = SubElement(eMetadata, 'Metaitem')
                eMetaitem.set('key', k)
                eMetaitem.text = str(v)
                       
    ePlots = SubElement(eProject, "Plots")
    for plot in project.plots:
        ePlot = SubElement(ePlots, plot.__class__.__name__)
        SIV(ePlot, 'key', plot.rget('key'))
        SIV(ePlot, 'title', plot.rget('title'))

        comment = plot.rget('comment')
        if comment is not None:
            eComment = SubElement(ePlot, "comment")
            eComment.text = comment

        eLayers = SubElement(ePlot, "Layers")
        for layer in plot.layers:
            
            eLayer = SubElement(eLayers, "Layer")
            SIV(eLayer, 'type', layer.rget('type'))
            SIV(eLayer, 'grid', layer.rget('grid'))
            SIV(eLayer, 'title', layer.rget('title'))
            SIV(eLayer, 'visible', layer.rget('visible'))
                            
            for (key, axis) in layer.axes.iteritems():
                eAxis = SubElement(eLayer, "Axis")
                eAxis.set('key', key)
                SIV(eAxis, 'label', axis.rget('label'))
                SIV(eAxis, 'scale', axis.rget('scale'))
                SIV(eAxis, 'start', axis.rget('start'))
                SIV(eAxis, 'end', axis.rget('end'))
                SIV(eAxis, 'format', axis.rget('format'))

            legend = layer.legend
            if legend is not None:
                eLegend = SubElement(eLayer, "Legend")
                SIV(eLegend, 'label', legend.rget('label'))
                SIV(eLegend, 'position', legend.rget('position'))
                SIV(eLegend, 'visible', legend.rget('visible'))
                SIV(eLegend, 'border', legend.rget('border'))
                SIV(eLegend, 'x', legend.rget('x'))
                SIV(eLegend, 'y', legend.rget('y'))
                                     
            for line in layer.lines:
                eLine = SubElement(eLayer, "Line")

                SIV(eLine, 'label', line.rget('label'))
                SIV(eLine, 'style', line.rget('style'))
                SIV(eLine, 'marker', line.rget('marker'))
                SIV(eLine, 'visible', line.rget('visible'))

                # For the line source we must check first
                # if this is not a temporary source.
                # TODO: if it was a temporary source we either
                # need to ignore the source (current situation)
                # or add the temporary dataset to the project.
                if line.source is not None:
                    if project.has_dataset(key=line.source.key):
                        SIV(eLine, 'source', line.source.rget('key'))
                    else:
                        logger.warn("Invalid line source. Skipped source.")
                
                SIV(eLine, 'width', line.rget('width'))

                SIV(eLine, 'cx', line.rget('cx'))
                SIV(eLine, 'cy', line.rget('cy'))
                SIV(eLine, 'row_first', line.rget('row_first'))
                SIV(eLine, 'row_last', line.rget('row_last'))
                SIV(eLine, 'cxerr', line.rget('cxerr'))
                SIV(eLine, 'cyerr', line.rget('cyerr'))

            # layer.labels
            if len(layer.labels) > 0:
                eLabels = SubElement(eLayer, "Labels")
                for label in layer.labels:
                    eLabel = SubElement(eLabels, "Label")
                    SIV(eLabel, 'x', label.rget('x'))
                    SIV(eLabel, 'y', label.rget('y'))
                    SIV(eLabel, 'system', label.rget('system'))
                    SIV(eLabel, 'valign', label.rget('valign'))
                    SIV(eLabel, 'halign', label.rget('halign'))
                    eLabel.text = label.rget('text')

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
        exporter_ascii = ExporterRegistry['ASCII']()
        
        dsdir = os.path.join(tempdir, 'datasets')
        os.mkdir(dsdir)
        for ds in spj.datasets:
            try:
                dspath = os.path.join(dsdir, dataset_filename_ascii(ds.key))
                exporter_ascii.write_to_file(dspath, ds.data)
                
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
