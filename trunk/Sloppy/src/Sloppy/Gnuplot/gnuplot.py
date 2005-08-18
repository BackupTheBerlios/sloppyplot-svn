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
Gnuplot Backend
"""



from subprocess import Popen, PIPE, STDOUT
import string, tempfile, os, shutil

import logging
logger = logging.getLogger('Gnuplot.gnuplot')

from Sloppy.Base import objects
from Sloppy.Base.dataset import Dataset
from Sloppy.Base.dataio import ExporterRegistry
from Sloppy.Base.backend  import BackendRegistry
from Sloppy.Base import backend, utils, uwrap

from terminal import XTerminal, DumbTerminal, PostscriptTerminal

from Sloppy.Lib import Signals

#class Builder:
#    def build(self): pass
    
    
class Backend(backend.Plotter):

    tmpdir = None  
    tmpfiles = []  # list of files that have been created by this class

    def init(self):
        self.encoding = self.options.get('encoding', 'iso_8859_15')
        self.window_title = "gnuplot-%s" % id(self)
        self.current_dir = None

        self.tmpdir = tempfile.mkdtemp(prefix="spl-gp-")
        self.tmpfiles = []
        # key: ds, value = (filename, change_counter_on_last_save)
        self.exports = {}

    
    def connect(self):
        logger.debug( "Opening new gnuplot session." )

        self.terminal = self.options.get('terminal', None)
        if self.terminal is None:
            self.terminal = DumbTerminal()
        
        # Note that due to 'close_fds=False', we will keep the connection
        # alive until we actively disconnect it.
        # TODO: how do we actually disconnect?
        cmd_list = ["gnuplot"]
        if self.options.get('persist',False):
            logger.debug("Enabling persistance!")
            cmd_list[0] += ' -persist'
                   
	p = Popen(cmd_list,shell=True,stdin=PIPE,stdout=PIPE,stderr=STDOUT,close_fds=False )
	(self.gpwrite,self.gpout) = (p.stdin, p.stdout)
        self.process = p
        self.history = list()

        logger.debug("gnuplot.py: creating tempfile: %s" % self.tmpdir)
        backend.Plotter.connect(self)

    def disconnect(self):
        logger.debug("Closing gnuplot session.")
        try:
            # closing gnuplot will cause an IOError, since gpwrite won't
            # be able to write any more.
            self("exit")
        except IOError:
            pass

        try:
            shutil.rmtree(self.tmpdir)
        except OSError:
            logger.warn("Temporary directory %s not available!" % self.tmpdir)
        else:
            logger.debug("gnuplot.py: deleted tmpfile %s" % self.tmpdir)
            
        backend.Plotter.disconnect(self)

    #----------------------------------------------------------------------
    # methods that a Plotter might want to re-implement

    def cd(self, dirname):
        """
        Change directory of Plotter process to `dirname`, which
        may also be a file name or a relative path name.
        """
        dirname = os.path.abspath(os.path.dirname(dirname))
        self.current_dir = dirname
        self('cd "%s"' % self.current_dir)
        
    def pwd(self):
        """
        Return absolute path name of the working directory used by the
        Plotter process.
        """
        return self.current_dir


        
    def __call__(self, cmd):
        """Send string to gnuplot"""

        encoded_cmd = cmd.encode( self.encoding )
        #encoded_cmd = cmd
        self.gpout.flush()
        Signals.emit(self, 'gnuplot-send-cmd', cmd=cmd)
        self.gpwrite.write(encoded_cmd + "\n")
        self.gpwrite.write("print '<--END-->'\n")
        self.gpwrite.flush()

        result = []
        while result[-1:] != ["<--END-->\n"]:
            if self.process.poll() is not None:                
                break
            result.append( self.gpout.readline() )

        if len(result) == 0:
            result = None
        elif result[-1:] == ["<--END-->\n"]:
            result = result[:-1]
            
        self.history.append( (encoded_cmd, result) )
        Signals.emit(self, 'gnuplot-finish-cmd', cmd=cmd, result=result)
        return result
            

    def getvar(self,var,convert_method=string.atof):
        """
	Get a gnuplot variable. 
	
	Returns a string containing the variable's value or None,
        if the variable is not defined.
	
	You may specify a method to convert the resultant parameter, e.g.
	>>> gp = Gnuplot()
	>>> gp("a = 10")
	>>> gp.getvar("a") # implies string.atof
	>>> gp.getvar("a", string.atof)
	>>> gp.getvar("a", string.atoi)
	>>> go.getvar("a", None) # no conversion -> returns String
        """
        self(" set print \"-\"\n")      # print output to stdout
        self(" if (defined(%s)) print %s ; else print \"None\" \n" % (var,var))
        result=self.gpout.readline()
        self(" set print\n")            # print output to default stderr
        if result[0:4]=="None":
            return None
	elif convert_method is not None:
	    return convert_method(result)
	else:
	    return(result)

    #----------------------------------------------------------------------
    # EXPORT FILE HANDLING
    
    def mark_for_export(self, source):
        """        
        Adds the given source to the list of datasets that need to be
        exported. Returns filename that the exported Dataset will
        have.
        """
        if not isinstance(source, Dataset):
            logger.error("Invalid source given. Not a Dataset.")
            return None
        
        # The format of self.exports is:
        #  key: source object (=> id)
        #  value: (filename, dataset_change_counter, dataset object)
        if self.exports.has_key(source) is False:
            logger.debug("Marking %s for export" % source)
            filename = source.key
            new_export = [filename, -1, source]
            self.exports[source] = new_export
            return new_export[0]
        else:
            return self.exports[source][0]
            
        
    #----------------------------------------------------------------------
    def clear(self):
        self('reset')

    def build_layer(self, layer, group_info):
        """
        Returns a list of gnuplot commands that need to be executed
        to draw this layer.
        group_info is a dictionary containing information for grouped lines.        
        """

        rv = []

        # visible
        if uwrap.get(layer, 'visible') is False:
            return rv
        
        # title
        title = uwrap.get(layer, 'title')
        if title is not None: rv.append('set title "%s"' % title)
        else: rv.append("unset title")

        # grid
        grid = uwrap.get(layer, 'grid')
        if grid is True: rv.append('set grid')
        else: rv.append('unset grid')

        # legend (aka key in gnuplot)
        legend = uwrap.get(layer, 'legend')
        if legend is not None:            
            visible = uwrap.get(legend, 'visible')
            if visible is True:
                # legend label (aka title in gnuplot)
                label = uwrap.get(legend, 'label')
                if label is not None: key_title = 'title "%s"' % label
                else: key_title = ""

                # legend border
                border = uwrap.get(legend, 'border')
                if border is True: key_border = "box"
                else: key_border = "nobox"

                # legend positioning
                position_mapping = {
                    'center' : 'graph 0.5, graph 0.5',
                    'lower left' : 'graph 0.0, graph 0.0',
                    'center right' : 'graph 1.0, graph 0.5',
                    'upper left' : 'graph 0.0, graph 1.0',
                    'center left' : 'graph 0.0, graph 0.5',
                    'upper right' : 'graph 1.0, graph 1.0',
                    'lower right' : 'graph 1.0, graph 0.0',
                    'upper center' : 'graph 0.5, graph 1.0',
                    'lower center' : 'graph 0.5, graph 0.0',
                    'outside' : 'outside'
                    }
                pos = uwrap.get(legend, 'position')
                if pos == 'best':
                    key_pos = ''
                elif pos == 'at position':
                    if legend.x is None and legend.y is None:
                        key_pos = ''
                    else:
                        x = uwrap.get(legend, 'x')
                        y = uwrap.get(legend, 'y')
                        key_pos = 'graph %.2f, graph %.2f' % (x, y)
                else:
                    key_pos = position_mapping[pos]

                rv.append("set key %(key_pos)s %(key_title)s %(key_border)s" % locals())
            else:
                rv.append("unset key")                

        # axes
        for key, axis in layer.axes.iteritems():            
            # axis format
            format = uwrap.get(axis, 'format')
            if format is not None: rv.append('set format %s "%s"' % (key, format))
            else: rv.append('set format %s' % key)

            # axis label
            label = uwrap.get(axis, 'label')
            if label is not None: rv.append('set %slabel "%s"' % (key, label))
            else: rv.append('unset %slabel' % key)

            # axis range
            start = uwrap.get(axis, 'start','*')
            end = uwrap.get(axis, 'end','*')
            rv.append('set %srange [%s:%s]' % (key,start,end))

            # axis scale
            scale = uwrap.get(axis, 'scale')
            if scale == 'linear': rv.append('unset log %s' % key)
            elif scale == 'log': rv.append('set log %s' % key)
            else:
                logger.error("Axis scale '%s' not supported by this backend." % scale)

        # lines
        line_cache = []
        for line in layer.lines:
            if uwrap.get(line, 'visible') is False: continue

            # mark source for export 
            filename = self.mark_for_export(uwrap.get(line, 'source'))
            if filename is None:
                continue
            source = '"%s"' % filename
            
            # title-clause
            label = uwrap.get(line, 'label')
            if label is not None: title = 'title "%s"' % label
            else: title = 'notitle'

            # using-clause
            # TODO: only do this if we have a group
            # TODO: on the other hand, we should only advance
            # TODO: cx/cy if we are talking about the same source!
            if 1 == 0:
                cx = line.cx or group_info.get('cx', 1)
                group_info['cx'] = cx + 2
                cy = line.cy or group_info.get('cy', 2)
                group_info['cy'] = cy + 2
            else:
                (cx, cy) = (line.cx, line.cy)
                if cx is None or cy is None:
                    logger.error("No source cx or cy given. Line skipped.")
                    continue
            using = 'using %s:%s' % (cx+1,cy+1)

            # TODO: support 'style' and 'marker'
            # with-clause
            type = uwrap.get(line, 'style')
            type_mappings = {'solid': 'w l'}
            try:
                with = type_mappings[type]
            except KeyError:
                with = ''
                logger.error('line type "%s" not supported by this backend.' % type )

            # line width
            width = uwrap.get(line, 'width')
            width = 'lw %s' % str(width)
            
            # merge all of the above
            line_cache.append( " ".join([source,using,with,width,title]) )

        # construct plot command from line_cache
        if len(line_cache) > 0:
            rv.append("plot " + ",\\\n".join(line_cache))
            #rv = "\n".join(rv)
            return rv
        else:            
            logger.warn("Emtpy layer!")
            return []



            
    def redraw(self, rebuild_cache=True):

        # All commands for gnuplot are appended to the cmd_list,
        # so that they can be executed at the very end.
        cmd_list = []
        cmd_list.append('cd "%s"' % self.tmpdir)
	cmd_list.append( "set encoding %s" % self.encoding )

        cmd_list += self.terminal.build(self)     

        # multiplot ?
        if len(self.plot.layers) > 1:
            cmd_list.append( "set multiplot" )
            for layer in self.plot.layers:
                group_info = {}
                x, y = uwrap.get(layer, 'x'), uwrap.get(layer, 'y')
                width, height = uwrap.get(layer, 'width'), uwrap.get(layer, 'height')
                cmd_list.append("set origin %.2f,%.2f" % (x,y))
                cmd_list.append("set size %.2f,%.2f" % (width, height))
                cmd_list += self.build_layer(layer, group_info)
            cmd_list.append( "unset multiplot" )
        else:
            # Single plot!
            # create plotting commands from the Layer information
            group_info = {}
            cmd_list += self.build_layer(self.plot.layers[0], group_info)


        # Export Datasets to temporary directory, so that
        # gnuplot can access them.
        exporter = ExporterRegistry.new_instance('ASCII')
        
        destdir = self.tmpdir
        for (source, value) in self.exports.iteritems():
            (filename, change_counter, ds) = value
            if ds is None:
                logger.warn("One of the Datasets to export is None.")
                continue
            if ds.is_empty():
                logger.warn("One of the Datasets to export is empty")
                continue
            logging.debug("Change counter %d, old %d" % (ds.change_counter, change_counter))
            if ds.has_changes(change_counter):                              
                filename = os.path.join(destdir, filename)
                logger.debug('exporting "%s" to dir "%s"' % (ds, destdir))            
                exporter.write_to_file(filename, ds.data)
                self.exports[source][1] = ds.change_counter
            else:
                logger.info("Dataset has not changed and is not exported!")
                
       
        # Now execute all collected commands.
        print "cmd list is: "
        for cmd in cmd_list:
            print "   ", cmd
        print
        
        Signals.emit(self, 'gnuplot-start-plotting')
        logger.info("Gnuplot command list:\n\n%s" % "\n".join(cmd_list))
        for cmd in cmd_list:
            self(cmd)

        Signals.emit(self,'gnuplot-after-plot', window_title=self.window_title)
        
    draw = redraw        
        


# ======================================================================

class BackendDumb(Backend):

    def __init__(self, *args, **kwargs):
        kwargs.update({'terminal' : DumbTerminal(), 'encoding' : 'iso_8859_15'})
        Backend.__init__(self, *args, **kwargs)

class BackendX11(Backend):
    def __init__(self, *args, **kwargs):
        kwargs.update({'terminal' : XTerminal(), 'encoding' : 'iso_8859_15'})
        Backend.__init__(self, *args, **kwargs)

        
BackendRegistry.register('gnuplot', Backend)
BackendRegistry.register('gnuplot/dumb', BackendDumb)
BackendRegistry.register('gnuplot/x11', BackendX11)



