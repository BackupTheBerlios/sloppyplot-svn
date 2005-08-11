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

# $HeadURL: file:///home/nv/sloppysvn/trunk/Sloppy/src/Sloppy/Base/project.py $
# $Id: project.py 430 2005-08-03 20:07:56Z nv $



class AbortIteration(Exception):
    pass



class ProgressList:

    def __init__(self, objects):
        self.objects = objects
        self.index = -1
        self.maxindex = len(objects)
        self.do_abort = False
        self.is_successful = True

    def next(self):
        if self.do_abort is True:
            raise AbortIteration
        
        self.index += 1
        if self.index >= self.maxindex:
            raise StopIteration
        else:    
            return self.objects[self.index]
    
    def __iter__(self):
        return self
    
    def fail(self, msg=None):
        pass

    def succeed(self):
        pass

    def finish(self):
        self.is_successful = True

    def abort(self):
        self.do_abort = True
        self.is_successful = False
        

class SimpleProgressList(ProgressList):

    def next(self):
        name = ProgressList.next(self)        
        print "Working on %s" % name,
        return name
    

    def fail(self, msg=None):
        print "[FAILED: %s]" % msg or "unknown error"

    def succeed(self):
        print "[OK]"

    def finish(self):
        print "--- End Of Operation ---"


def test():

    filenames = ['file A', 'file B', 'file C']

    pi = SimpleProgressList(filenames)
    for filename in pi:
        print filename
        pi.succeed()


    
if __name__ == "__main__":
    test()
