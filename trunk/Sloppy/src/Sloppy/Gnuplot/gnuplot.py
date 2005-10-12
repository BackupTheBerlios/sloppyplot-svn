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
from Sloppy.Base import utils, backend

from terminal import XTerminal, DumbTerminal, PostscriptTerminal

from Sloppy.Lib import Signals


    
class Backend(backend.Backend):

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

        # X-perimental
        self.layer_to_axes = {}
        self.axes_to_layer = {}
        self.layers_cache = [] # copy of self.plot.layers
        self.layer_signals = {}
        
        self.line_caches = {}
        self.omaps = {}

        # we keep an instance var 'cmd_list' which contains all commands
        # in the order that they should be executed
        self.cmd_list = []
        self.cmd_dict = {}

    
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
        backend.Backend.connect(self)

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
            
        backend.Backend.disconnect(self)



    #----------------------------------------------------------------------
    # methods that a Backend might want to re-implement
    #
    
    def cd(self, dirname):
        """
        Change directory of Backend process to `dirname`, which
        may also be a file name or a relative path name.
        """
        dirname = os.path.abspath(os.path.dirname(dirname))
        self.current_dir = dirname
        self('cd "%s"' % self.current_dir)
        
    def pwd(self):
        """
        Return absolute path name of the working directory used by the
        Backend process.
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


    def export_datasets(self):
        # Export Datasets to temporary directory, so that
        # gnuplot can access them.
        exporter = ExporterRegistry['ASCII']()
        
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
        if layer.visible is False:
            return rv
        
        # title
        title = layer.title
        if title is not None: rv.append('set title "%s"' % title)
        else: rv.append("unset title")

        # grid
        grid = layer.grid
        if grid is True: rv.append('set grid')
        else: rv.append('unset grid')
        
        rv.extend(self.update_legend(layer))
        rv.extend(self.update_axes(layer))
        rv.extend(self.update_labels(layer))
        rv.extend(self.update_lines(layer))

        return rv


            
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
                x, y = layer.x, layer.y
                width, height = layer.width, layer.height
                cmd_list.append("set origin %.2f,%.2f" % (x,y))
                cmd_list.append("set size %.2f,%.2f" % (width, height))
                cmd_list += self.build_layer(layer, group_info)
            cmd_list.append( "unset multiplot" )
        else:
            # Single plot!
            # create plotting commands from the Layer information
            group_info = {}
            cmd_list += self.build_layer(self.plot.layers[0], group_info)

        self.export_datasets()
       
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
        

    #######################################################################
    # reimplementation

    """
    One idea:

    When you call an update function, then the cmd_list is regenerated.

    If you want to replot everything, then you can just execute all
    commands in the order of cmd_list.

    Alternatively, if update_layer gets an updateinfo and updates only
    parts, then it will move the commands needed to update these few
    things into a cmd_queue, which then must be executed by the calling
    function!
    
    """

    def update_axes(self, layer, updateinfo={}):
        # updateinfo is ignored
        cl = []
        # axes
        for key, axis in layer.axes.iteritems():            
            # axis format
            format = axis.format
            if format is not None: cl.append('set format %s "%s"' % (key, format))
            else: cl.append('set format %s' % key)

            # axis label
            label = axis.label
            if label is not None: cl.append('set %slabel "%s"' % (key, label))
            else: cl.append('unset %slabel' % key)

            # axis range
            start = axis.get_value('start', '*')
            end = axis.get_value(axis, 'end','*')
            cl.append('set %srange [%s:%s]' % (key,start,end))

            # axis scale
            scale = axis.scale
            if scale == 'linear': cl.append('unset log %s' % key)
            elif scale == 'log': cl.append('set log %s' % key)
            else:
                logger.error("Axis scale '%s' not supported by this backend." % scale)

        self.cmd_dict['axes'] = cl                
        return cl

    
    def update_lines(self, layer, updateinfo={}):
        # updateinfo is ignored

        cl = []
        # lines
        line_cache = []
        for line in layer.lines:
            try:
                if line.visible is False: continue

                ds = self.get_line_source(line)
                table = self.get_table(ds)
                cx, cy = self.get_column_indices(line)
                
                # mark source for export            
                filename = self.mark_for_export(ds)
                if filename is None:
                    continue
                source = '"%s"' % filename

                label = self.get_line_label(line, table=table, cy=cy)
                if label is not None: title = 'title "%s"' % label
                else: title = 'notitle'

                using = 'using %s:%s' % (cx+1,cy+1)

                # TODO: support 'style' and 'marker'
                # with-clause
                type = line.style
                type_mappings = {'solid': 'w l'}
                try:
                    with = type_mappings[type]
                except KeyError:
                    with = ''
                    logger.error('line type "%s" not supported by this backend.' % type )

                # line width
                width = line.width
                width = 'lw %s' % str(width)
            except backend.BackendError, msg:
                logger.error("Error while processing line: %s" % msg)
                continue
            else:
                # merge all of the above into a nice gnuplot command
                line_cache.append( " ".join([source,using,with,width,title]) )

        # construct plot command from line_cache
        if len(line_cache) > 0:
            cl.append("plot " + ",\\\n".join(line_cache))
            #rv = "\n".join(rv)
            self.cmd_dict['lines'] = cl
            return cl
        else:            
            logger.warn("Emtpy layer!")
            self.cmd_dict['lines'] = []            
            return []


    def update_legend(self, layer, updateinfo={}):
        # updateinfo is ignored

        cl = []
        #:legend
        # (aka key in gnuplot)
        legend = legend.layer
        if legend is not None:
            #:legend.visible
            visible = legend.visible
            if visible is True:
                #:legend.label
                label = legend.label
                if label is not None: key_title = 'title "%s"' % label
                else: key_title = ""

                #:legend.border:OK
                border = legend.border
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
                pos = legend.position
                if pos == 'best':
                    key_pos = ''
                elif pos == 'at position':
                    if legend.x is None and legend.y is None:
                        key_pos = ''
                    else:
                        x,y = legend.x, legend.y
                        key_pos = 'graph %.2f, graph %.2f' % (x, y)
                else:
                    key_pos = position_mapping[pos]

                cl.append("set key %(key_pos)s %(key_title)s %(key_border)s" % locals())
            else:
                cl.append("unset key")                

        self.cmd_dict['legend'] = cl
        return cl


    def update_labels(self, layer, updateinfo={}):

        cl = []
        #:layer.labels
        for label in layer.labels:                                    
            if label.system == 0: # 0: data
                coords = "at first %.2f, first %.2f" % (label.x, label.y)
            elif label.system == 1: # 1: graph
                coords = "at graph %.2f, graph %.2f" % (label.x, label.y)

            map_align = {0:'center', 1:'left', 2:'right'}
            align = map_align[label.halign]
            cl.append('set label "%s" %s %s' % (label.text, coords, align) )

        self.cmd_dict['labels'] = cl
        return cl

        
    def update_layer(self, layer):        
        pass
    
    def Xdraw(self):
        self.check_connection()
        logger.debug("Gnuplot.draw")                
             
        ##if self.plot.layers != self.layers_cache:
        ##    self.arrange()

        # TODO: build layers_cache
        #for

        # clear command list
        cd = self.cmd_dict = []

        cd['tempdir'] = ['cd "%s"' % self.tmpdir]
        cd['encoding'] = ['set encoding %s' % self.encoding]
        cd['terminal'] = [self.terminal.build(self)]
        
        for layer in self.plot.layers:
            self.update_layer(layer)

        self.execute_queue()


    def build_queue(self):
        # right now we will build the complete cmd_dict in a certain
        # order.  The long term goal should be, that the update functions
        # not only update the appropriate section in the cmd_dict, but
        # also provide some simple commands to replace the data, e.g.
        # if a label is removed, then the appropriate label line would
        # be removed from cmd_dict['labels'].  At the same time, the
        # cmd_queue should contain something like 'unset label xxx'.
        # Of course this requires a lot more work, so this is nothing
        # for now.
        #
        
        # 'lines' is last and contains the plot commands
        order = ['tempdir', 'encoding', 'terminal', 'axes', 'labels', 'layer',
                 'lines']

    def execute_queue(self):
        pass



# ======================================================================

class BackendDumb(Backend):

    def __init__(self, *args, **kwargs):
        kwargs.update({'terminal' : DumbTerminal(), 'encoding' : 'iso_8859_15'})
        Backend.__init__(self, *args, **kwargs)

class BackendX11(Backend):
    def __init__(self, *args, **kwargs):
        kwargs.update({'terminal' : XTerminal(), 'encoding' : 'iso_8859_15'})
        Backend.__init__(self, *args, **kwargs)


backend.BackendRegistry['gnuplot'] = Backend
backend.BackendRegistry['gnuplot/dumb'] = BackendDumb
backend.BackendRegistry['gnuplot/x11'] = BackendX11



