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
logger = logging.getLogger('Base.classregistry')



class ClassWrapper:
    def __init__(self, klass, *args, **kwargs):
        self.klass = klass
        self.args = args
        self.kwargs = kwargs

    def new_instance(self, *args, **kwargs):
        all_args = self.args + args
        all_kwargs = self.kwargs.copy()
        all_kwargs.update(kwargs)        
        return self.klass(*all_args, **all_kwargs)
        

class Registry:

    def __init__(self, label="Unnamed Registry"):
        self._wrappers = {}
        self.label = label


    def register(self, key, klass, *args, **kwargs):
        if self._wrappers.has_key(key) is True:
            raise KeyError("You cannot register any class more than once (key was '%s')" % key)
        self._wrappers[key] = ClassWrapper(klass, *args, **kwargs)
   
    def remove(self, key):
        self._wrappers.pop(key)

    def get_class(self, key):
        return self._wrappers[key].klass
    
    def iterkeys(self): return self._wrappers.iterkeys()
    def iteritems(self): return self._wrappers.iteritems()
    def itervalues(self): return self._wrappers.itervalues()

    
    def has_key(self, key):
        return self._wrappers.has_key(key)

    has_class = has_key

    
    def new_instance(self, key, *args, **kwargs):
        return self._wrappers[key].new_instance(*args, **kwargs)


    def __str__(self):
        rv = []
        rv.append("-"*78)
        rv.append("%s\n" % self.label)
        rv.append("\n")
        for k,v in self._wrappers.iteritems():
            rv.append( " %20s: %s, %s, %s" % (k, v.klass, v.args, v.kwargs) )
        rv.append("")
        return "\n".join(rv)                       
