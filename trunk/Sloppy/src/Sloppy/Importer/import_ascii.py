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


import re

from Sloppy.Base.dataset import Dataset
from Sloppy.Base import dataio, globals

from Sloppy.Lib.Props import *

import numpy

import logging
logger = logging.getLogger('import.ascii')


#------------------------------------------------------------------------------
DS={
'import_ascii:designations':
"""Designations for the imported columns.
If more than the given columns exists, then
the expression is repeated, e.g.  if you have
designations 'XY' and five columns, then
their designations will be XYXYX.
The split sign | indicates that only the last
part of it will be repeated, e.g. X|Y would
yield XYYYY for the same five columns."""
}


#------------------------------------------------------------------------------            
class Importer(dataio.Importer):

    author = "Niklas Volbers"

    #----------------------------------------------------------------------
    # Properties
    #

    # Prefixes
    #  header_
    #  data_
    #  result_

    # Suffixes
    #  ln  (linenumber)
    #  re  (regular expression)
    #  

    # Header
    header_size = \
     VP(
        Integer,
        VRange(0, None),
        None,
        default=None,
        blurb="Header size",
        doc="Number of header lines"
        )

    header_end_re = \
     String(
        default='\s*[+-]?\d+.*',
        doc="Regular expression that indicates the end of the header (if header size is not set)"
        )

    header_include_end = \
     Boolean(
        default=False,
        doc="Whether to include the last line of the header in the header"
        )

    header_keys_ln = \
      VP(
        Integer,
        VRange(0,None),
        None,
        default=None,
        blurb="Key line",
        doc="Number of the line that contains the column keys"
        )

    header_keysplit_re = \
     String(
        blurb="Key split expression",
        default="\s*,\s*",
        doc="Regular expression that splits up the column keys."
        )

    header_keytrim_re = \
     String(
        blurb="Key trim expression",
        default='\s*[#]?\s*(?P<keys>.*)\s*',
        doc="Regular expression that trims the key line before splitting it up"
        )

    header_metadata_re = \
     String(
        blurb="Header metadata expression",
        default = '\s*[\#]?\s*(?P<key>.*?)\s*:\s*(?P<value>.*)\s*',
        doc = "Regular expression to match metadata key-value pairs."
        )
    
    # Data 

    
    # Other
    
    delimiter = \
    String(
        blurb ="Delimiter",
        doc="Column delimiter that separates the columns"
        )
       
    ncols = \
     VP(
        Integer,
        VRange(0,None),
        None,
        default=None,
        blurb="Columns",
        doc="Number of columns",
        )


    dataset = VP(Instance(Dataset), None, default=None)

    designations = \
     VP(
        ['X', 'Y', 'X|Y', 'XY'],
        default='X|Y',        
        blurb="Designations",
        doc=DS['import_ascii:designations']
        )

    typecodes = \
     VP(list, basestring,
        default='d'
        )

    growth_offset = \
     IntegerRange(
        10,None,
        default=100
        )
    
    #----
    public_props = ['delimiter', 'ncols', 'header_size',
                    'header_keys_ln', 'designations']

    

    #----------------------------------------------------------------------
    # Reading in Data
    #
    
    def read_dataset_from_stream(self, fd):

        if self.dataset is None:
            self.dataset = Dataset()
            self.dataset._array = None
            
        self.parse_header(fd)
        self.parse_body(fd)        
        logger.info("Finished reading ASCII file.")

        return self.dataset

    def parse_header(self, fd):
        """
        Parse the header of the stream, i.e. the part with the result_metadata.
        The attribute self.dataset must be a valid Dataset.
        """

        metadata = {}

        # compile regular expressions
        def safe_compile(expression):
            try:
                return re.compile(expression)
            except:
                logger.error("Failed to compile regular expression: %s" % expression)
                raise

        cr_keytrim = safe_compile(self.header_keytrim_re)
        cr_keysplit = safe_compile(self.header_keysplit_re)
        cr_end = safe_compile(self.header_end_re)
        cr_metadata = safe_compile(self.header_metadata_re)

        # function to extract metadata from header line
        def parse_line(line, n, metadata):
            if n == self.header_keys_ln:
                # try to extract key names
                m = cr_keytrim.match(line)
                if m is None:
                    logger.info("Column keys could not be trimmed.")
                else:
                    line = m.groupdict()['keys']
                metadata['_import_keys'] = [key for key in cr_keysplit.split(line)]
                logger.info("Found column keys: %s", metadata['_import_keys'])

            else:
                # try to extract metadata
                m = cr_metadata.match(line)
                if m is not None:
                    gd = m.groupdict()
                    k,v = gd['key'], gd['value']
                    logger.info("Found metadata: %s = %s" % (k,v) )
                    metadata[k] = v

        #
        # Parsing the header:
        #

        # - How long is the header?
        #   -> if header_size is given, then we assume that
        #      the header is that many lines long
        #   -> if header_end_re is given, then we assume that
        #      the header stops when the given regular expression
        #      matches
        #   -> header_end_re has a default value, which matches
        #      if a number appears.
        #   -> The regular expression can either be part of the header
        #      or can be the first non-header line. The var
        #      self.header_include indicates this.

        metadata = {}
        line = "--"
        n = 1 # current line
        header_size = self.header_size
        if header_size is not None:
            # skip header_size
            while header_size > 0 and len(line) > 0:
                line = fd.readline()
                parse_line(line,n, metadata)
                header_size -= 1
                n += 1
        else:
            # skip until regular expression is matched
            while len(line) > 0:
                pos = fd.tell()
                line = fd.readline()
                match = cr_end.match(line)
                if match is not None:
                    # rewind if the match does not belong to the header
                    if self.header_include_end is False:
                        fd.seek(pos)
                    else:
                        n+=1
                    break
                parse_line(line,n, metadata)
                n += 1

        metadata['_import_headersize'] = n
        self.dataset.node_info.metadata.update(metadata)
        

    def parse_body(self, fd):
        """
        Parse the body of the stream, i.e. the data part.
        The attribute self.dataset must be a valid Dataset.
        However, if it does not contain an array, then an array
        is constructed.
        """

        ds = self.dataset
        
        # Used compiled regular expressions (cr_):
        #  cr_trim used to remove comments, linebreaks, whitespace, ...
        #  cr_split used to split the remaining row into its fields
        #  cr_comment used to identify a comment-only line
        cr_trim = re.compile('^\s*(.*?)(#.*)?$')
        #cr_split is set below, after the delimiter has been determined
        cr_comment = re.compile('^\s*(#.*)?$')

        # skip comments
        line = '#'
        while len(line) > 0 and cr_comment.match(line) is not None:
            rewind = fd.tell()
            line = fd.readline()
        fd.seek(rewind)

        # determine delimiter
        delimiter = self.delimiter
        if delimiter is None or len(delimiter) == 0:
            # determine from first non-comment line
            rewind = fd.tell()
            line = fd.readline()
            if line.find(',') != -1:
                delimiter = ','
            else:
                delimiter = '[\s\t]*'
            fd.seek(rewind)

        logger.debug("determined delimiter: '%s'" % delimiter)
        
        if ds._array == None:
            # determine optional arguments
            typecodes = self.typecodes
            ncols = self.ncols
            
            # if no column count is given, try to
            # determine nr. of ncols from first line
            if ncols is None:
                rewind = fd.tell()
                line = fd.readline()

                # split off comments
                try:
                    line = cr_trim.match(line).groups()[0]
                except AttributeError:
                    ncols = 2

                cregexp = re.compile(delimiter)
                matches = [match for match in cregexp.split(line) if len(match) > 0]
                logger.debug("MATCHES = %s" % str(matches))
                ncols = len(matches)
               
                fd.seek(rewind)

            # create new array for Dataset

            # column names 
            hkeys = ds.node_info.metadata.get('_import_keys',[])
            if len(hkeys) == ncols:
                # either reuse header keys
                names = hkeys
            else:
                # or construct new names
                names = []
                for i in range(ncols):
                    names.append('col%d' % i)

            formats = []
            for i in range(ncols):
                formats.append('f4')
                #formats.append(numpy.float32)

            # TODO: the array should be created by the dataset,
            # TODO: not by this function. This way, the dataset
            # TODO: could ignore the formats and return a homogeneous
            # TODO: array. After all, we don't want to write two
            # TODO: import functions!

            # ds.new_array(shape=(self.growth_offset,),
            #              names=names, formats=formats)
            dtype = numpy.dtype({'names': names, 'formats':formats})
            a = numpy.zeros( (self.growth_offset,), dtype=dtype)
            ds._array = a
       
        logger.debug("# of columns to be expected: %d" % ds.ncols)

        # make sure existing Dataset has at least one entry.
        if ds.nrows == 0:
            ds.resize(1)

        #
        # set up type converters that convert the given values
        # to the required field type
        #                
        types = [ds.get_field_ptype(name) for name in ds.names]

        # Assign field designations.
        # If there are more fields than designations, then
        # the designation is extended to the desired length, e.g.
        # for a dataset with 6 fields:
        #   X   -> XXXXXX
        #   XY  -> XYXYXY        
        #   X|Y -> XYYYYY        
        designations = self.designations
        if designations.find('|') != -1:
            designations, repeat_pattern = designations.split('|')
        else:
            repeat_pattern = designations
            
        while len(designations) < ds.ncols:
            designations += repeat_pattern
        logger.debug("Column designations: %s" % designations)

        # set designations
        for n in range(ds.ncols):
            ds.get_info(n).designation = designations[n]
        
        #
        # read in file line by line
        #
        logger.debug("Start reading ASCII file.")
        cr_split = re.compile(delimiter)
        skipcount = 0
        rownr = 0
        row = fd.readline()        
        while len(row) > 0:

            # Split off comments using a regular expression.
            # This is a more robust solution than the former
            #  row = row.split('#')[0]

            # TODO: Be careful when we have string fields, then a #
            # TODO: might not be what it looks like -- it might be
            # TODO: contained in quotes!
            
            try:
                row = cr_trim.match(row).groups()[0]
            except AttributeError:
                logger.error("Skipped row: %s" % row)
                row = fd.readline()
                continue

            matches = [match for match in cr_split.split(row) if len(match) > 0]

            #logger.debug("MATCHES = %s" % str(matches))
            if len(matches) == 0:
                skipcount += 1
                if skipcount > 100:
                    # TODO: implement question!
                    #Signals.emit("ask-for-confirmation", "Warning: More than 100 lines skipped recently. Should we continue with this file?")
                    skipcount = 0
            else:
                try:
                    # before the string is converted to a number, we
                    # convert all '-' occurences to numpy.nan
                    matches = [(m,numpy.nan)[m=='-'] for m in matches]
                    values = tuple(map(lambda x, t: t(x), matches, types))
                except ValueError, msg:                    
                    #logger.warn("Skipped: %s (%s)" % (row,msg))
                    row = fd.readline()
                    continue
                except TypeError, msg:
                    #logger.warn("Skipped: %s (%s)" % (row,msg))
                    row = fd.readline()
                    continue
                else:
                    #logger.info("Read %s" % values)
                    pass

                #logger.debug("Setting row %d to %s" % (rownr, str(values)))
                ds._array[rownr] = values
                
                # Move to next row.
                # If this is the last row, then the Dataset is extended.
                if rownr+1 >= ds.nrows:
                    ds.extend(ds.nrows+self.growth_offset)

                rownr += 1

            row = fd.readline()

        # Resize dataset to real size, i.e. the number
        # of rows that have actually been read.
        ds.resize(nrows=rownr)


#------------------------------------------------------------------------------
globals.importer_registry['ASCII'] = Importer

globals.import_templates['ASCII'] = \
  dataio.IOTemplate(blurb="ASCII", extensions='dat,txt',
                    importer_key='ASCII', is_internal=True)

