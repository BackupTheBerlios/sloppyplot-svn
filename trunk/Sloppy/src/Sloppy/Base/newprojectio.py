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

import logging
logger = logging.getLogger('Base.newprojectio')


from Sloppy.Base.dataset import Dataset
from Sloppy.Base.project import Project
from Sloppy.Base.dataio import ExporterRegistry, read_table_from_stream
from Sloppy.Base.table import Table, Column
from Sloppy.Base.objects import *
from Sloppy.Base.dataio import read_table_from_file


from Sloppy.Lib.ElementTree.ElementTree import ElementTree, Element, SubElement, parse, tostring

from Numeric import *
from pycdf import *




def toElement(project):

    def safe_set(element, key, value):
        if value is not None: # and isinstance(value, basestring):
            element.set(key, str(value))    

    eProject = Element("Project")
    ###eProject.attrib['version'] = FILEFORMAT

    eDatasets = SubElement(eProject, "Datasets")
    for ds in project.datasets:
        if ds.get_data() is None:
            raise RuntimeError("EMPTY DATASET '%s'" % ds.key)
        
        if isinstance(ds.data, Table):
            tbl = ds.data
            
            eData = SubElement(eDatasets, 'Table')            
            safe_set(eData, 'cols', tbl.ncols)
            safe_set(eData, 'typecodes', tbl.typecodes_as_string)
            
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
        ePlot = SubElement(ePlots, plot.getClassName())
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
                safe_set(eLine, 'cxerr', line.cxerr)
                safe_set(eLine, 'cyerr', line.cyerr)
            

    # beautify the XML output by inserting some newlines
    def insert_newlines(element):
        element.tail = '\n'
        if element.text is None:
            element.text = "\n"
        for sub_element in element.getchildren():
            insert_newlines(sub_element)
#    insert_newlines(eProject)
        
    return eProject



def write_dataset(fd, ds):
    
    data = ds.get_data()
    key = ds.key

    # TODO: add dataset metadata

    
    if isinstance(data, Table):
        dim_x = fd.def_dim( "%s_x" % key, data.ncols )
        dim_y = fd.def_dim( "%s_y" % key, data.nrows )
        var = fd.def_var( key, NC.FLOAT, (dim_y, dim_x))
        for n in range(data.ncols):
            var[n:] = data[n]

        # add Column properties
        for j in range(data.ncols):
            column = data.get_column(j)
            for k in ['key', 'designation', 'label', 'query']:
                v = column.get_value(k)
                if v is not None:
                    setattr(var, "%s:%s" % (k, j), v)
            
    else:
        raise TypeError("Only Tables can be saved right now.")
    
def save_project(project, filename=None, path=None):
    " Write the whole project to a file.  Return True on success. "

    fd = CDF(filename, NC.WRITE|NC.CREATE)
    fd.automode()

    for ds in project.datasets:
        write_dataset(fd, ds)
        
    xml = toElement(project)
    setattr(fd, 'XML', tostring(xml, encoding="utf-8"))
    

    fd.close()



def demo_zno():

    ds = Dataset(key = "ZnO-10-Abs1")
    ds.data = read_table_from_file("../../../Examples/Data/zn10abs1.abs", "ASCII", delimiter='\t')

    tbl = ds.data
    tbl.column(0).set_values('key', 'Wavelength', 'label', 'Wavelength (nm)')
    tbl.column(1).set_values(key='Absorption', designation = 'Y', label='Optical Absorption (arb. units)')
    
    layer = Layer(type='line2d',
                  lines=[Line(source=ds)],
                  axes = {'x': Axis(label="Wavelength [nm]"),
                          'y': Axis(label="Absorption [a.u.]")})
                          
    pl = Plot(label=u"Optical Absorption of ZnO Quantum Dots",
              layers=[layer], key=ds.key)
    
    spj = Project(plots=[pl], datasets=[ds])

    save_project(spj, 'zno.spj')


if __name__ == "__main__":
    demo_zno()
