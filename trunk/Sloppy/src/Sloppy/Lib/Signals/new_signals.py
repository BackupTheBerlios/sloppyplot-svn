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

""" Signal/Slot mechanism for SloppyPlot. """


import weakref
import inspect

import logging
logger = logging.getLogger('Signals')



class AnonymousReceiver:
    pass
class SignalError(Exception):
    pass


class Signal:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class Callback:
    
    def __init__(self, cb, *args, **kwargs):
        
        if inspect.ismethod(cb) is True:
            # method 
            self.receiver = weakref.ref(cb.im_self)
            self.callback = cb.im_func
        else:
            # function
            self.receiver = (lambda: AnonymousReceiver)
            self.callback = cb

        self.args = args
        self.kwargs = kwargs

        
                 
class HasSignals:

    def __init__(self):
        self._signals = {} # dictionary of Signal objects (keys: signal names)
        self._callbacks = {} # dictionary of callbacks (keys: signal names)

    def sig_register(self, signal):
        self._signals[signal] = Signal()
        self._callbacks[signal] = []
        
    def sig_connect(self, signal, callback, *args, **kwargs):
        print "Connect!"        
        self.sig_check(signal)
        self._callbacks[signal].append(Callback(callback, *args, **kwargs))

    def sig_emit(self, signal, *args, **kwargs):
        print "Emit!"        
        self.sig_check(signal)
        deprecated = []
        
        for cb in self._callbacks[signal]:
            all_args = args + cb.args
            all_kwargs = kwargs.copy()
            all_kwargs.update( cb.kwargs )
            
            # returns None if referenced object does not exist anymore
            receiver = cb.receiver()
            
            if receiver is None:
                logger.debug("emit: receiver for signal is gone. signal marked for deletion.")
                deprecated.append(cb)
                continue

            try:
                if receiver == AnonymousReceiver:
                    cb.callback(self, *all_args, **all_kwargs)
                else:
                    cb.callback(receiver, self, *all_args, **all_kwargs)
            except:
                print ("Caught exception while trying to call callback [%s,%s,%s] during emission of signal '%s'." %
                                  (receiver, all_args, all_kwargs, self))
                raise

        # remove all obsolete signals
        for cb in deprecated:
            logger.debug("emit: -- removing Callback --")
            self._callbacks.pop(signal)
            


    def sig_check(self, signal):
        if self._signals.has_key(signal) is False:
            raise SignalError("Signal '%s' is not registered for object '%s'" % (signal, self))        


#------------------------------------------------------------------------------
def test():
    class TestClass(HasSignals):
        def on_notify(self, sender, value):
            print "Class Receiver received value %s" % value
    def receiver(sender, value):
        print "Signal with value %s" % value
        
        
    tc = TestClass()
    tc.sig_register("notify")

    tc.sig_connect("notify", receiver)
    tc.sig_connect("notify", tc.on_notify)
    tc.sig_emit("notify", 10)
    
    
if __name__ == "__main__":
    test()
    
