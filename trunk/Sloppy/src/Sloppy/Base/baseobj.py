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


from Sloppy.Lib.Signals import *
from Sloppy.Lib.Check import *


class BaseObject(HasChecks, HasSignals):
       
    def __init__(self, **kwargs):
        HasChecks.__init__(self, **kwargs)
        HasSignals.__init__(self)
        
        # set up available Signals       
        self.signals['update'] = Signal()

        # The update::key signals are different for normal attributes
        # and for List/Dict attributes, which have their own on_update
        # method. It is necessary to use new_lambda, because in case of
        #  self._values[key].on_update = lambda ....
        # the lambda would be redefined with each iteration and
        # every List/Dict object would emit the same signal.        
        
        def new_lambda(key):
            return lambda sender, updateinfo: self.sig_emit('update::%s'%key, key, updateinfo)

        for key, check in self._checks.iteritems():
            self.signals['update::%s'%key] = Signal()            
            if isinstance(check, (List,Dict)):
                self._values[key].on_update = new_lambda(key)                 

        # trigger Signals on attribute update
        def on_update(sender, key, value):
            self.sig_emit('update::%s'%key, key, value)           
            self.sig_emit('update', [key])
        self.on_update = on_update


    def set(self, *args, **kw):
        """ Set the given attribute(s) to specified value(s).

        You may pass an even number of arguments, where one
        argument is the attribute name and the next one the
        attribute value. You may also pass this as keyword
        argument, i.e. use the key=value notation.

        Returns a dictionary of changed keys with their old values.
        """
        checks = self._checks
        changes = {}

        # Make sure that all the given keys are valid
        for arg in args:
            arglist = list(args)
            while len(arglist) > 1:
                key = arglist.pop(0)
                value = arglist.pop(0)
                if checks.has_key(key) is False:
                    raise KeyError(key)
                changes[key] = value
                            
        for key, value in kw.iteritems():
            if checks.has_key(key) is False:
                    raise KeyError(key)
            changes[key] = value

        # assign changes to object; old values are saved 
        changeset = {}
        for key, value in changes.iteritems():
            changeset[key] = self._values[key]
            checks[key].set(self, key, value) # TODO: maybe catch exceptions?

        self.sig_emit('update', changeset.keys())
        return changeset


