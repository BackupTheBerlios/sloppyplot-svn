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

""" Notification mechanism for SloppyPlot. """


import weakref
import inspect

import logging
logger = logging.getLogger('Lib.Signals')


class AnonymousReceiver:
    pass
class SignalError(Exception):
    pass


class Signal:
    def __init__(self):
        pass
    

class Callback:
    
    def __init__(self, owner, signal, cb, *args, **kwargs):
        
        if inspect.ismethod(cb) is True:
            # method 
            self.receiver = weakref.ref(cb.im_self)
            self.func = cb.im_func
        else:
            # function
            self.receiver = (lambda: AnonymousReceiver)
            self.func = cb

        self.args = args
        self.kwargs = kwargs

        self.signal = signal
        self.owner = owner


    def disconnect(self):
        self.owner.sig_disconnect(self)
        
                 
class HasSignals:

    def __init__(self):
        self._signals = {} # dictionary of Signal objects (keys: signal names)
        self._callbacks = [] # list of all callbacks


    def sig_register(self, signal):
        self._signals[signal] = Signal()

        
    def sig_connect(self, signal, func, *args, **kwargs):
        logger.debug("Connecting '%s' to signal '%s' of object '%s'." % (func, signal, object.__str__(self)))
        self.sig_check(signal)
        cb = Callback(self, signal, func, *args, **kwargs)
        self._callbacks.append(cb)
        return cb

    
    def sig_disconnect(self, cblist):
	if not isinstance(cblist, (list,tuple)):
	    cblist = [cblist]

        for cb in cblist:
            logger.debug("Disconnecting callback '%s' of object '%s'." % (cb, object.__str__(self)))
            try:
                self._callbacks.remove(cb)
            except ValueError, msg:
                logger.debug("Could not remove callback %s: %s" % (cb,msg))


    def sig_disconnect_all(self):
        for cb in self._callbacks:
            logger.debug("Disconnecting callback '%s' of object '%s'." % (cb, object.__str__(self)))
            try:
                self._callbacks.remove(cb)
            except ValueError, msg:
                logger.debug("Could not remove callback %s: %s" % (cb,msg))


    def sig_cblist(self, signal=None, receiver=None, func=None):
        cblist = self._callbacks

        if signal is not None:
            cblist = [cb for cb in cblist if cb.signal == signal]            

        if receiver is not None:
            cblist = [cb for cb in cblist if id(cb.receiver) == id(receiver)]

        if func is not None:
            if inspect.ismethod(func):
                cblist = [cb for cb in cblist if cb.func == func.im_func]
            else:
                cblist = [cb for cb in cblist if cb.func == func]

        return cblist
                                
                    
    def sig_emit(self, signal, *args, **kwargs):

        self.sig_check(signal)
        deprecated = []

        logger.debug("Emitting signal '%s' of object '%s'." % (signal, object.__str__(self)))
        for cb in [c for c in self._callbacks if c.signal == signal]:
            all_args = args + cb.args
            all_kwargs = kwargs.copy()
            all_kwargs.update( cb.kwargs )
            
            # returns None if referenced object does not exist anymore
            receiver = cb.receiver()
            
            if receiver is None:
                logger.debug("emit: receiver for signal is gone. callback marked for deletion.")
                deprecated.append(cb)
                continue

            logger.debug("  => Callback to function '%s' of '%s'" % (cb.func, object.__str__(cb.receiver)))
            
            try:
                if receiver == AnonymousReceiver:
                    cb.func(self, *all_args, **all_kwargs)
                else:
                    cb.func(receiver, self, *all_args, **all_kwargs)
            except:
                print ("Caught exception while trying to call callback [%s,%s,%s] during emission of signal '%s'." %
                                  (object.__str__(receiver), all_args, all_kwargs, self))
                raise

        # remove all obsolete signals
        for cb in deprecated:
            logger.debug("emit: -- removing Callback --")
            self._callbacks.remove(cb)            


    def sig_check(self, signal):
        if self._signals.has_key(signal) is False:
            raise SignalError("Signal '%s' is not registered for object '%s'." % (signal, object.__str__(self)))


#------------------------------------------------------------------------------
def test():
    class TestClass(HasSignals):
        def __init__(self):
            HasSignals.__init__(self)
            self.sig_register("notify")
            
        def on_notify(self, sender, value):
            print "Class Receiver received value %s" % value

            
    def receiver(sender, value):
        print "Signal with value %s" % value                
        
    tc = TestClass()
    tc2 = TestClass()

    tc.sig_connect("notify", receiver)
    tc.sig_connect("notify", tc2.on_notify)
    tc.sig_emit("notify", 10)

    del tc2
    tc.sig_emit("notify", 12)

    del receiver
    tc.sig_emit("notify", 8)
    #----------

    tc = TestClass()
    cb = tc.sig_connect("notify", tc.on_notify)
    tc.sig_emit("notify", 14)
    tc.sig_disconnect(cb)
    tc.sig_emit("notify", 16)
    #----------
    tc = TestClass()
    tc.sig_connect("notify", tc.on_notify)
    tc.sig_connect("notify", tc.on_notify)
    tc.sig_connect("notify", tc.on_notify)
    tc.sig_emit("notify", 18)
    cblist = tc.sig_cblist(func=tc.on_notify)
    tc.sig_disconnect(cblist)
    tc.sig_emit("notify", 20)

    #----------
    #tc.sig_connect("notfy", tc.on_notify) # a misspelled signal!
    
    
    
if __name__ == "__main__":
    test()
    
