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



from Sloppy.Base.dataset import Dataset, Table
from Sloppy.Base.project import Project
from Sloppy.Base.objects import Legend, Axis, Plot, Layer, Line, TextLabel
from Sloppy.Base import pdict, iohelper, error, globals, utils
from Sloppy.Base.dataio import read_dataset_from_stream

from Sloppy.Lib.ElementTree.ElementTree import ElementTree, Element, SubElement, parse

import tarfile, tempfile, os, shutil
import numpy

import logging
logger = logging.getLogger('Base.projectio')
#------------------------------------------------------------------------------

FILEFORMAT = "0.5.2"


class ParseError(Exception):
    pass


#------------------------------------------------------------------------------
# Object Creation (starting with new_xxx)


def new_table(spj, element):

    # Create field infos
    formats = []
    info_dict = {}
    for eColumn in element.findall('Column'):        
        # name
        try:
            name = eColumn.attrib['name']
        except KeyError:
            logger.warn("Could not get column name; using default name instead.")
            name = utils.unique_names(['col'], info_dict.keys())
        
        # format
        try:
            format = eColumn.attrib['format']
        except KeyError:
            logger.warn("Could not get column type, using default type instead.")
            format = 'f4'
        formats.append(format)

        # create info with attributes
        info = Table.Info()        
        for eAttribute in eColumn.findall('Attribute'):
            key = eAttribute.attrib['key']
            value = eAttribute.text
            if value is not None:
                info.set_value(key, value)       
        info_dict[name] = info
        
        
    # create table with given format and infos, but w/o any rows
    a = numpy.zeros((0,), {'names':info_dict.keys(), 'formats':formats})
    tbl = Table(a, info_dict)

    # node info
    for eItem in element.findall('NodeInfo/Item'):
        key = eItem.attrib['key']
        value = eItem.text
        if value is not None:
            tbl.node_info.set_value(key, value)

    for eItem in element.findall('NodeInfo/MetaItem'):
        key = eItem.attrib['key']
        value = eItem.text
        if value is not None:
            tbl.node_info.metadata[key] = value


    # table key is essential
    try:
        key = element.attrib['key']
    except KeyError:
        logger.warn("Could not get table key. Using generic key instead.")
        key = pdict.unique_key(spj.datasets, 'dataset')
    tbl.key = key


    # Right now, the Table is still empty. By setting this callback
    # for the _import attribute, the dataset is loaded from the hard
    # disk on the next access.    
    filename = os.path.join('datasets', utils.as_filename(tbl.key))           
    def do_import(the_table):
        try:
            archive = tarfile.open(spj.get_filename(),'r:gz')
        except tarfile.ReadError:
            logger.error('Error while opening archive "%s"' % filename)
            raise FileNotFoundError
        
        tempdir = tempfile.mkdtemp(prefix="spj-temp-")
        try:
            archive.extract(filename, tempdir)
            importer = globals.importer_registry['ASCII'](dataset=the_table)
            return importer.read_dataset_from_file(os.path.join(tempdir, filename))
        finally:
            shutil.rmtree(tempdir)

    tbl._import = do_import

    return tbl
        


        
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

    # If we encounter an older file format, then we simply transform
    # the XML to the new format.
    version = eProject.get('version', None)
    def raise_version(new_version):
        logger.info("Converted SloppyPlot Archive to version %s" % new_version)
        return new_version
    
    while (version is not None and version != FILEFORMAT):
        if version=='0.5':
            # Datasets.Table.Column.Info -> Datasets.Table.Column.Attribute
            for element in eRoot.findall('Datasets/Table/Column/Info'):
                element.tag = 'Attribute'            
            version = raise_version('0.5.2')
            continue
        raise IOError("Invalid Sloppy File Format Version %s. Aborting Import." % version)

    # load datasets
    for eDataset in eProject.findall('Datasets/Table'):
        spj.datasets.append( new_table(spj, eDataset))

    # load plots
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

    eData = SubElement(eProject, "Datasets")
    for ds in project.datasets:
        
        if ds._array is None:
            logger.error("Empty Dataset: %s. NOT SAVED." % ds.key)
            continue

        # Table
        if isinstance(ds, Table):
            tbl = ds
            eTable = SubElement(eData, 'Table')

            # All information about the columns is stored in the
            # element tree.  Only the actual data will later on be
            # written to the archive.
            for n in range(tbl.ncols):
                eColumn = SubElement(eTable, 'Column')
                SIV(eColumn, 'name', tbl.get_name(n))
                dt = tbl.get_column_dtype(n)
                SIV(eColumn, 'format', '%s%s' % (dt.kind, str(dt.itemsize)))
                info = tbl.get_info(n)
                for k,v in info.get_values().iteritems():
                    if v is not None:
                        eAttribute = SubElement(eColumn, 'Attribute')
                        SIV(eAttribute, 'key', k)
                        eAttribute.text = v

            # general information (should be there for any other kind of
            # Dataset as well)
            SIV(eTable, 'key', ds.key)
            SIV(eTable, 'fileformat', 'CSV' )

            # write node information
            node_items = tbl.node_info.get_keys()
            node_items.remove('metadata')
            iohelper.write_dict(eTable, 'NodeInfo', tbl.node_info.get_values(include=node_items))
            iohelper.write_dict(eTable, 'NodeInfo', tbl.node_info.metadata)
        else:
            logger.error("Cannot save Dataset %s of type %s" % (ds.key, ds.__class__.__name__))
                                   
    ePlots = SubElement(eProject, "Plots")
    for plot in project.plots:
        ePlot = SubElement(ePlots, plot.__class__.__name__)
        SIV(ePlot, 'key', plot.key)
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
                        SIV(eLine, 'source', line.source.key)
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







#------------------------------------------------------------------------------

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
        exporter_ascii = globals.exporter_registry['CSV']()
        
        dsdir = os.path.join(tempdir, 'datasets')
        os.mkdir(dsdir)
        for ds in spj.datasets:
            try:
                dspath = os.path.join(dsdir, utils.as_filename(ds.key))
                exporter_ascii.write_to_file(dspath, ds)
                
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
