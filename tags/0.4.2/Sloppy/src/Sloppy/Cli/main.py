

import logging
logging.basicConfig()

from Sloppy.Base.project import *
from Sloppy.Base import const
from Sloppy.Backends import *

import os.path
from optparse import OptionParser


#------------------------------------------------------------------------------

def load_file(filename):
    try:
        logging.info("Loading %s" % filename)
        return create_project_from_file(filename)
    except IOError:
        logging.error("File not found error.")
        raise SystemExit


#------------------------------------------------------------------------------
   
parser = OptionParser(version="%prog 1.0")

parser.add_option("-f","--file",dest="filename",
                  help="specify filename of project to use")
parser.add_option("-q","--quiet",action="store_true", dest="verbose",
                  help="don't print status messages to stdout")
parser.add_option("-d","--debug",action="store_true", dest="debug",
                  default=True,help="print debug messages to stdout")


args = ["-f", os.path.join(const.internal_path(const.PATH_EXAMPLE),"zno.spj"), "plot"]
(options,args) = parser.parse_args(args)

#------------------------------------------------------------------------------
# process options
logging.debug("Supplied options: %s" % options)

logger = logging.getLogger('')
if options.debug is True:
    print "(debug mode)"
    logger.setLevel(logging.DEBUG)
else:
    if options.verbose is False:
        print "(quiet mode)"
        logger.setLevel(logging.WARNING)
    else:
        print "(normal mode)"
        logger.setLevel(logging.INFO)


    
#------------------------------------------------------------------------------
# process arguments

while len(args) > 0:    
    arg = args.pop()

    if arg == "dump":
        logging.info("Dump !")
        if not options.filename:
            raise MissingArgument
        print load_file(options.filename)
    elif arg == "plot":
        logging.info("Plot !")
        if not options.filename:
            raise MissingArgument
        project = load_file(options.filename)
        # get first plot
        plots = project.plots
        if len(plots) == 0:
            print "No plot found!"
            raise SystemExit
        # open plotting backend
        p = BackendRegistry.new(backend='gnuplot/x11',
                                project=project,
                                plot=plots[0],
                                persist = True)
        p.draw()
    else:
        print "Unknown command: ", arg
    





