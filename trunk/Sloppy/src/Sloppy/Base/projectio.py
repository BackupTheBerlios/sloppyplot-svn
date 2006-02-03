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
from Sloppy.Base import pdict, iohelper
from Sloppy.Base.dataio import exporter_registry, read_table_from_stream
from Sloppy.Base import error

from Sloppy.Lib.ElementTree.ElementTree import ElementTree, Element, SubElement, parse

import tarfile, tempfile, os, shutil


#------------------------------------------------------------------------------
import logging
logger = logging.getLogger('Base.projectio')


FILEFORMAT = "0.5.2"

"""
File format history:

  - 0.3 -> 0.4: Table.cols -> Table.ncols  (transformation implemented)

  - 0.4 -> 0.4.3: added layer.labels (no conversion required)

  - 0.4.5 -> 0.5: changed internal file format to netCDF.
    This is an incompatible change, so I decided to drop the
    prior conversions for 0.4.6. Sorry, but this is what Alpha
    software really means.

  - 0.5 -> 0.5.2: implemented line.color.  Since line.color was not accessible
    through the GUI until then, there is no conversion of existing entries.
  
"""

class ParseError(Exception):
    pass


#------------------------------------------------------------------------------
# Object Creation (starting with new_xxx)


def new_dataset(spj, element):
    ncols = int(element.attrib.pop('ncols',0))
    typecodes = element.attrib.pop('typecodes','')

    # TODO: pass fileformat_version to importer (somehow)
    # TODO: how?
    fileformat = element.attrib.pop('fileformat', 'CSV')
    fileformat_version = element.attrib.pop('fileformat_version', None)
    ds = Dataset(**element.attrib)

    # metadata
    for eMetaitem in element.findall('Metadata/Metaitem'):
        key = eMetaitem.attrib['key']
        value = eMetaitem.text
        ds.node_info.metadata[key] = unicode(value)

#     # actual Table
#     if element.tag == 'Table':

#         # Extract additional column information.
#         # This information will be passed on to 'set_table_import',
#         # which will pass it on to the internal importer.        
#         column_props = list()
#         for i in range(ncols):
#             column_props.append(dict())
        
#         for eColumn in element.findall('Column'):
#             n = int(eColumn.get('n'))
#             p = column_props[n]
#             for eInfo in eColumn.findall('Info'):
#                 key = eInfo.get('key', None)
#                 if key is not None:
#                     p[key] = unicode(eInfo.text)
        
#         filename = os.path.join('datasets', utils.as_filename(ds.key))
#         ds.set_table_import(spj, filename, typecodes, column_props, fileformat)
        
    
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
        
    # create new layer
    layer = Layer(**element.attrib)

#     # group properties
#     group_properties = {}
#     eGroups = element.find('Groups')
#     if eGroups is not None:
#         # We iterate over all group properties and look for elements
#         # with tags that match the group property's classname, e.g.
#         # <GroupLineMarker>...</GroupLineMarker> for the Property
#         # Layer.marker.
#         keys = ['group_linestyle', 'group_linewidth', 'group_linecolor', 'group_linemarker']
#         for key in keys:
#             classname = layer.get_value(key).__class__.__name__
#             groupclass = layer.get_value(key).__class__
#             eGroup = eGroups.find(classname)
#             if eGroup is not None:
#                 eGroup.attrib['type'] = int(eGroup.attrib['type'])
#                 group_properties[key] = groupclass(**eGroup.attrib)
#                 print "CYCLE LIST", group_properties[key].cycle_list

#     layer.set_values(**group_properties)

    # TODO: test type and _then_ assign the data    
    for eLine in element.findall('Line'):        
        layer.lines.append(new_line(spj, eLine))        
    
    # axes
    for eAxis in element.findall('Axis'):
        key = eAxis.attrib.pop('key', 'x')
        a = Axis(**eAxis.attrib)
        if key == 'x':
            layer.xaxis = a
        elif key == 'y':
            layer.yaxis = a

    # legend
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



#------------------------------------------------------------------------------

def fromTree(tree):
    eProject = tree.getroot()
                    
    spj = Project()

    version = eProject.get('version', None)
    def raise_version(new_version):
        logger.info("Converted SloppyPlot Archive to version %s" % new_version)
        return new_version
    
    while (version is not None and version != FILEFORMAT):
        if version=='0.5':
            version = raise_version('0.5.2')
            continue
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
            element.set(key, unicode(value))


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
            # key and the data to the element tree, so we don't
            # need to put that information into the data file.
            n = 0
            for column in tbl.get_columns():
                kw = column.get_values(exclude=['data'],default=None)
                if len(kw) > 0:
                    eColumn = SubElement(eData, 'Column')
                    SIV(eColumn, 'n', n)
                    for k,v in kw.iteritems():
                        if v is not None:
                            eInfo = SubElement(eColumn, 'Info')
                            SIV(eInfo, 'key', k)
                            eInfo.text = v                            
                n += 1
                
            
        else:
            raise RuntimeError("Invalid dataset", ds)
        
        SIV(eData, 'key', ds.get('key'))
        SIV(eData, 'fileformat', 'CSV' )

        # TODO: iohelper.write_dict, but then I need a transformation
        # TODO: of the file format: Metaitem -> Item
        if len(ds.metadata) > 0:
            eMetadata = SubElement(eData, "Metadata")
            for k,v in ds.node_info.metadata.iteritems():
                eMetaitem = SubElement(eMetadata, 'Metaitem')
                eMetaitem.set('key', k)
                eMetaitem.text = str(v)
                       
    ePlots = SubElement(eProject, "Plots")
    for plot in project.plots:
        ePlot = SubElement(ePlots, plot.__class__.__name__)
        SIV(ePlot, 'key', plot.get('key'))
        SIV(ePlot, 'title', plot.get('title'))

        comment = plot.get('comment')
        if comment is not None:
            eComment = SubElement(ePlot, "comment")
            eComment.text = comment

        eLayers = SubElement(ePlot, "Layers")
        for layer in plot.layers:
            
            eLayer = SubElement(eLayers, "Layer")
            attrs = layer.get_values(['type', 'grid', 'title', 'visible'], default=None)            
            iohelper.set_attributes(eLayer, attrs)

#             # group properties
#             eGroups = SubElement(eLayer, "Groups")

#             def groups_to_element(eGroups, keys):
#                 for key in keys:
#                     print "Writing group property ", key                
#                     group = layer.get_value(key)
#                     if group is not None:
#                         groupname = group.__class__.__name__
#                         eGroup = SubElement(eGroups, groupname)
#                         # TODO: cycle_list is missing, because it is a list!
#                         attrs = group.get_values(include=['type','value', 'range_start', 'range_stop', 'range_step'],
#                                      default=None)
#                         iohelper.set_attributes(eGroup, attrs)
                        
#             groups_to_element(eGroups, ['group_linestyle',
#                                         'group_linemarker',
#                                         'group_linewidth',
#                                         'group_linecolor'])
                
            # axes
            for (key, axis) in layer.axes.iteritems():
                eAxis = SubElement(eLayer, "Axis")
                attrs = axis.get_values(['label', 'scale', 'start', 'end', 'format'],default=None)
                attrs['key'] = key
                iohelper.set_attributes(eAxis, attrs)

            # legend
            legend = layer.legend
            if legend is not None:
                eLegend = SubElement(eLayer, "Legend")
                attrs = legend.get_values(['label','position','visible','border','x','y'],default=None)
                iohelper.set_attributes(eLegend, attrs)

            # lines
            for line in layer.lines:
                eLine = SubElement(eLayer, "Line")

                # For the line source we must check first
                # if this is not a temporary source.
                # TODO: if it was a temporary source we either
                # need to ignore the source (current situation)
                # or add the temporary dataset to the project.
                if line.source is not None:
                    if project.has_dataset(key=line.source.key):
                        SIV(eLine, 'source', line.source.get('key'))
                    else:
                        logger.warn("Invalid line source. Skipped source.")
                
                attrs = line.get_values(['width','label','style','marker','visible', 'color','marker_color', 'marker_size', 'cx','cy','row_first','row_last','cxerr','cyerr'],default=None)
                iohelper.set_attributes(eLine, attrs)

            # layer.labels
            if len(layer.labels) > 0:
                eLabels = SubElement(eLayer, "Labels")
                for label in layer.labels:
                    eLabel = SubElement(eLabels, "Label")
                    attrs = label.get_values(['x','y','system','valign','halign'],default=None)
                    iohelper.set_attributes(eLabel, attrs)
                    eLabel.text = label.get('text')

    iohelper.beautify_element(eProject)
        
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
        exporter_ascii = exporter_registry['CSV']()
        
        dsdir = os.path.join(tempdir, 'datasets')
        os.mkdir(dsdir)
        for ds in spj.datasets:
            try:
                dspath = os.path.join(dsdir, utils.as_filename(ds.key))
                exporter_ascii.write_to_file(dspath, ds.data)
                
            except AttributeError:
                logger.error("Error while writing Dataset '%s'" % ds.key)
                raise
            except error.NoData:
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
                raise error.SloppyError('Error while creating archive "%s": %s' % (filename, msg))
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
