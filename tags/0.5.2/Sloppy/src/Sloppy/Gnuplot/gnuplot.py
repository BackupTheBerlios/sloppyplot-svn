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

from Sloppy.Base import objects, globals
from Sloppy.Base.dataset import Dataset
from Sloppy.Base import utils, backend

from Sloppy.Gnuplot.terminal import XTerminal, DumbTerminal, PostscriptTerminal

"""
Maybe it is even simpler!

queue.append( adict, key, cmd, unset_cmd )

- cmd is stored in adict[key]
- if the change is going to be immediate, then we call
    gp(unset_cmd)
    gp(set_cmd)

"""


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

        self.cdict = {}
        self.queue = []
        self.execution_order = [] # ?

        self.sig_register('gnuplot-send-cmd')
        self.sig_register('gnuplot-finish-cmd')
        
    
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
        self.gpout.flush()
        self.sig_emit('gnuplot-send-cmd', cmd=cmd)
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
        self.sig_emit('gnuplot-finish-cmd', cmd=cmd, result=result)
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
            filename = utils.as_filename(source.key)
            new_export = [filename, -1, source]
            self.exports[source] = new_export
            return new_export[0]
        else:
            return self.exports[source][0]


    def export_datasets(self):
        # Export Datasets to temporary directory, so that
        # gnuplot can access them.
        exporter = globals.exporter_registry['ASCII']()
        
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
                exporter.write_to_file(filename, ds)
                self.exports[source][1] = ds.change_counter
            else:
                logger.info("Dataset has not changed and is not exported!")                           
        
    #----------------------------------------------------------------------
    def clear(self):
        self('reset')

         

    #----------------------------------------------------------------------
    # Update Methods:
    #
    #  TODO: <explanation of the concept>
    #        Maybe better in the class itself, so it will be readable in
    #        the API documentation.
    #
    
    def update_axes(self, layer, updateinfo={}):
        # updateinfo is ignored
        cd = self.cdict[layer]        
        queue = self.queue
        
        cmd = []
        # axes
        for key, axis in layer.axes.iteritems():            
            # axis format
            format = axis.format
            if format is not None: cmd.append('set format %s "%s"' % (key, format))
            else: cmd.append('set format %s' % key)

            # axis label
            label = axis.label
            if label is not None: cmd.append('set %slabel "%s"' % (key, label))
            else: cmd.append('unset %slabel' % key)

            # axis range
            start = axis.get_value('start', '')
            end = axis.get_value('end','*')
            cmd.append('set %srange [%s:%s]' % (key,start,end))

            # axis scale
            scale = axis.scale
            if scale == 'linear': cmd.append('unset log %s' % key)
            elif scale == 'log': cmd.append('set log %s' % key)
            else:
                logger.error("Axis scale '%s' not supported by this backend." % scale)

        queue.append((cd, 'axes', cmd, None))

    
    def update_lines(self, layer, updateinfo={}):
        # updateinfo is ignored
        cd = self.cdict[layer]        
        queue = self.queue
        
        # lines
        line_cache = []        
        for line in layer.lines:
            index = len(line_cache)
            print "TRYING TO PLOT LINE #", index
            try:
                if line.visible is False: continue

                ds = self.get_line_source(line)
                cx, cy = self.get_column_indices(line)
                
                # mark source for export            
                filename = self.mark_for_export(ds)
                if filename is None:
                    continue
                source = '"%s"' % filename

                label = self.get_line_label(line, dataset=ds, cy=cy)
                if label is not None: title = 'title "%s"' % label
                else: title = 'notitle'

                using = 'using %s:%s' % (cx+1,cy+1)

                #
                # Group Properties
                #
                line_index = layer.lines.index(line)

                #:line.style
                #:layer.group_style
                style = layer.group_style.get(line, index, line.style)

                #:line.marker
                #:layer.group_marker
                marker = layer.group_marker.get(line, index, line.marker)
                print "-------", marker
                
                #:line.width
                #:layer.group_width                
                width = layer.group_width.get(line, index, line.width)

                #:line.color
                #:layer.group_color
                color = layer.group_color.get(line, index, line.color)

                #
                # with-clause
                #
                
                # the 'linestyle' is a line type in gnuplot
                linestyle_mappings = \
                  {'None'               : "with points",
                   "solid"              : "with linespoints",
                   "dashed"             : "with linespoints ls 1",
                   "dash-dot"           : "with linespoints ls 2",
                   "dotted"             : "with linespoints ls 3",
                   "steps"              : "with steps"
                   }                
                try:
                    with = linestyle_mappings[style]
                except KeyError:
                    with = ''
                    logger.error('line type "%s" not supported by this backend.' % type )


                print "###################"
                print with, "---", style
                print "###################"
                # line.marker
                linemarker_mappings = \
                {# 'None' is a special case treated below
                 "points"                  : "pt 1",
                 "pixels"                  : "pt 2",
                 "circle symbols"          : "pt 3",
                 "triangle up symbols"     : "pt 4",
                 "triangle down symbols"   : "pt 5",
                 "triangle left symbols"   : "pt 6",
                 "triangle right symbols"  : "pt 7",
                 "square symbols"          : "pt 8",             
                 "plus symbols"            : "pt 9",
                 "cross symbols"           : "pt 1",
                 "diamond symbols"         : "pt 2",
                 "thin diamond symbols"    : "pt 3",
                 "tripod down symbols"     : "pt 4",
                 "tripod up symbols"       : "pt 5",
                 "tripod left symbols"     : "pt 6",
                 "tripod right symbols"    : "pt 7",
                 "hexagon symbols"         : "pt 8",
                 "rotated hexagon symbols" : "pt 9",
                 "pentagon symbols"        : "pt 1",
                 "vertical line symbols"   : "pt 2",
                 "horizontal line symbols" : "pt 3"
                 }
                if marker == 'None':
                    with = with.replace('linespoints', 'lines')
                    point_type = ''
                else:
                    point_type = linemarker_mappings[marker] + " ps 2"
                
                # line width
                width = 'lw %s' % str(width)
            except backend.BackendError, msg:
                logger.error("Error while processing line: %s" % msg)
                continue
            else:
                # merge all of the above into a nice gnuplot command
                line_cache.append( " ".join([source,using,with,point_type,width,title]) )

        # construct plot command from line_cache
        if len(line_cache) > 0:
            cmd = "plot " + ",\\\n".join(line_cache)            
            queue.append((cd, 'lines', cmd, None))
        else:            
            logger.warn("Emtpy layer!")
            queue.append((cd, 'lines', None, None))


    def update_legend(self, layer, updateinfo={}):
        # updateinfo is ignored
        cd = self.cdict[layer]        
        queue = self.queue

        cmd = []
        #:legend
        # (aka key in gnuplot)
        legend = layer.legend
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

                cmd.append("set key %(key_pos)s %(key_title)s %(key_border)s" % locals())
            else:
                cmd.append("unset key")                

        queue.append((cd, 'legend', cmd, None))


    def update_labels(self, layer, updateinfo={}):
        # updateinfo is ignored
        cd = self.cdict[layer]        
        queue = self.queue

        #:layer.labels
        cmd = []
        for label in layer.labels:                                    
            if label.system == 'data':
                coords = "at first %.2f, first %.2f" % (label.x, label.y)
            elif label.system == 'graph':
                coords = "at graph %.2f, graph %.2f" % (label.x, label.y)
            else:
                logger.error("label has non-supported coordinate system %s" % label.system)
                return
            
            align = label.halign
            cmd += ['set label "%s" %s %s' % (label.text, coords, align)]

        queue.append((cd, 'labels', cmd, 'unset labels'))

        
    def update_layer(self, layer, updateinfo={}):
        # updateinfo is ignored
        cd = self.cdict[layer]        
        queue = self.queue
        
        # visible
        if layer.visible is False:
            queue.append((self.cdict, layer, {}, None))
            return
        
        # title
        title = layer.title
        if title is not None:
            queue.append((cd, 'title', 'set title "%s"' % title, None))
        else:
            queue.append((cd, 'title', None, 'unset title'))

        # grid
        grid = layer.grid
        if grid is True:
            queue.append((cd, 'grid', 'set grid', None))
        else:
            queue.append((cd, 'grid', None, 'unset grid'))
        
        self.update_legend(layer)
        self.update_axes(layer)
        self.update_labels(layer)
        self.update_lines(layer)


    
    def draw(self):
        self.check_connection()
        logger.debug("Gnuplot.draw")                

        cd = self.cdict = {}
        cd['start'] = {}
        cd['end'] = {}
        
        #
        # The command `queue` is a list of 4-tuples of the form
        #  (dictionary, key, set, unset)
        # which must be read in the following form:
        #
        # (1) If an `unset` operation is given, it can be executed
        #     immediately to remove the corresponding item from the
        #     gnuplot plot.  If e.g. the user decided to remove the plot
        #     title, then we could say 'unset title'.  This way we
        #     don't need to resend the whole command chain to gnuplot
        #     but only a single command.
        #
        # (2) If a `set` operation is given, then we assign
        #       dictionary[key] = set
        #     This is the gnuplot command that should be executed
        #     to do whatever is necessary (e.g. to set the plot title,
        #     'set title "Whatever"').  If `set` is None, then the item
        #     dictionary[key] is removed from the dictionary.
        #
        # Most often you will only use one of the two, e.g.
        #
        # Set the title to 'Whatever'. No need to unset anything:
        #   (cd, 'title', 'set title "Whatever"', None)
        #
        # Remove all labels:
        #   (cd, 'labels', None, 'unset labels')
        #
        # Remove only label 2 (assuming there were also labels 1 and 3).
        # Then it is also necessary to re-construct the command to draw
        # the other two labels:
        #   (cd, 'labels', 'set label 1 "One"\nset label 3 "Two"', 'unset label 2')
        #
        # Note: `cd` is the command dictionary of the corresponding layer.
        # 
        #
        queue = self.queue = []

        queue.append((cd, 'tempdir', 'cd "%s"' % self.tmpdir, None))
        queue.append((cd, 'encoding', 'set encoding %s' % self.encoding, None))
        queue.append((cd, 'terminal', self.terminal.build(self), None))

       
        # Create commands for each layer.  If we have multiple
        # layers, then we also need to add multiplot commands before
        # the first layer and after the last layer
        
        # multiplot ?
        if len(self.plot.layers) > 1:
            cd['multiplot-start'] = ["set multiplot"]
            cd['multiplot-end'] = ["unset multiplot"]
            for layer in self.plot.layers:
                # TODO: maybe add a command to the queue to clear cdict[layer]?
                self.cdict[layer] = {}
                self.update_layer(layer)

                x, y, width, height = layer.x, layer.y, layer.width, layer.height                
                self.cdict[layer]['multiplot-start'] = \
                  ["set origin %.2f,%.2f" % (x,y),
                  "set size %.2f,%.2f" % (width, height)]                
        else:
            # Single plot!
            # create plotting commands from the Layer information
            layer = self.plot.layers[0]
            self.cdict[layer] = {}
            self.update_layer(layer)


        def apply_queue(queue):
            logger.debug("Applying Queue...")
            while len(queue) > 0:
                adict, key, set, unset = queue.pop()

                if unset is not None:
                    print "Performing unset ", unset
                    self(unset)

                if set is not None:
                    adict[key] = set
                elif adict.has_key(key):
                    adict.pop(key)

        apply_queue(queue)


        #
        # determine execution order
        #
        order = self.execution_order = ['tempdir', 'encoding', 'terminal', 'multiplot-start']

        for layer in self.plot.layers:
            order.append(layer)

        order += ['title',
                  'grid',
                  'axes',
                  'labels',
                  'layer',
                  'lines',
                 'multiplot-end']
                
        print "QUEUE:"
        print cd

        logger.debug("Executing command dict...")
        self.export_datasets()
        self.execute(cd)

#         # The following snippet shows how to update a single attribute:        
#         print "---"
#         layer = self.plot.layers[0]
#         layer.title = None
#         self.update_layer(layer)
#         apply_queue(queue)
#         self("replot")
                


#self.execute_queue()

    redraw = draw

    def execute(self, item):
        def execute_list(alist):
            for item in alist:
                self.execute(item)
                
        def execute_dict(adict):
            for key in self.execution_order:
                if adict.has_key(key):
                    self.execute(adict[key])

        if isinstance(item, dict):
            execute_dict(item)
        elif isinstance(item, list):
            execute_list(item)
        else: # => should be a string
            print "Calling ", item
            self(item)
      
        




# ======================================================================

class BackendDumb(Backend):

    def __init__(self, *args, **kwargs):
        kwargs.update({'terminal' : DumbTerminal(), 'encoding' : 'iso_8859_15'})
        Backend.__init__(self, *args, **kwargs)

class BackendX11(Backend):
    def __init__(self, *args, **kwargs):
        kwargs.update({'terminal' : XTerminal(), 'encoding' : 'iso_8859_15'})
        Backend.__init__(self, *args, **kwargs)


globals.BackendRegistry['gnuplot'] = Backend
globals.BackendRegistry['gnuplot/dumb'] = BackendDumb
globals.BackendRegistry['gnuplot/x11'] = BackendX11



