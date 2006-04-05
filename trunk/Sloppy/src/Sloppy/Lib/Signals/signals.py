"""
This is a very simple and nice implementation of a Signals/Slot
mechanism. It was written by Patrick Chasco on July 26, 2005 and
was published as signals.py on ASPN.  It is licensed under the Python
license.
"""


from weakref import *
import inspect

import logging
logger = logging.getLogger('Lib.Signals')
#------------------------------------------------------------------------------


class Signal:
    """
    class Signal

    A simple implementation of the Signal/Slot pattern. To use, simply 
    create a Signal instance. The instance may be a member of a class, 
    a global, or a local; it makes no difference what scope it resides 
    within. Connect slots to the signal using the "connect()" method. 
    The slot may be a member of a class or a simple function. If the 
    slot is a member of a class, Signal will automatically detect when
    the method's class instance has been deleted and remove it from 
    its list of connected slots.
    """
    def __init__(self):
        self.slots = []

        # for keeping references to _WeakMethod_FuncHost objects.
        # If we didn't, then the weak references would die for
        # non-method slots that we've created.
        self.funchost = []

    def __call__(self, *args, **kwargs):
        deleted = 0
        for i in range(len(self.slots)):
            slot = self.slots[i - deleted]
            if slot != None:
                slot(*args, **kwargs)
            else:               
                del self.slots[i]
                deleted += 1
                
    def call(self, *args, **kwargs):
        self.__call__(*args, **kwargs)

    def connect(self, slot):
        self.disconnect(slot)
        if inspect.ismethod(slot):
            wm = WeakMethod(slot)
            self.slots.append(wm)
        else:
            o = _WeakMethod_FuncHost(slot)
            wm = WeakMethod(o.func)
            self.slots.append(wm)
            # we stick a copy in here just to keep the instance alive
            self.funchost.append(o)
        return wm
    
    def disconnect(self, slot):
        try:
            for i in range(len(self.slots)):
                wm = self.slots[i]
                if inspect.ismethod(slot):
                    if wm.f == slot.im_func and wm.c() == slot.im_self:
                        del self.slots[i]
                        return
                else:
                    if wm.c().hostedFunction == slot:
                        del self.slots[i]
                        return
        except:
            pass

    def disconnect_all(self):
        del self.slots
        del self.funchost
        self.slots = []
        self.funchost = []

class _WeakMethod_FuncHost:
    def __init__(self, func):
        self.hostedFunction = func
    def func(self, *args, **kwargs):
        self.hostedFunction(*args, **kwargs)

# this class was generously donated by a poster on ASPN (aspn.activestate.com)
class WeakMethod:
	def __init__(self, f):
            self.f = f.im_func
            self.c = ref(f.im_self)
	def __call__(self, *args, **kwargs):
            if self.c() == None : return
            try:
                self.f(self.c(), *args, **kwargs)
            except Exception, msg:
                raise
            #raise RuntimeError("Error while triggering signal (method %s): %s" % (self.c(), msg))
        def disconnect(self):
            self.c = lambda: None





class HasSignals:

    def __init__(self):
        self.signals = {}                    

    def sig_register(self, name):
        self.signals[name] = Signal()

    def sig_emit(self, name, *args, **kwargs):
        signal = self.signals[name]        
        logger.debug("Emit %s (%d slots)" % (name, len(signal.slots)))
        signal(self, *args, **kwargs)

    def sig_connect(self, name, func):
        
        return self.signals[name].connect(func)

    def sig_disconnect(self, name, slot):
        self.signals[name].disconnect(slot)

    def sig_disconnect_all(self):
        for signal in self.signals.itervalues():
            signal.disconnect_all()        



#========================================================
# Example usage
#========================================================
if __name__ == "__main__":
    class Button:
        def __init__(self):
            # Creating a signal as a member of a class
            self.sigClick = Signal()

    class Listener:
        # a sample method that will be connected to the signal
        def onClick(self):
            print "onClick ", repr(self)
    
    # a sample function to connect to the signal
    def listenFunction():
        print "listenFunction"
   
    # a function that accepts arguments
    def listenWithArgs(text):
        print "listenWithArgs: ", text

    b = Button()
    l = Listener()
    
    # Demonstrating connecting and calling signals
    print
    print "should see one message"
    b.sigClick.connect(l.onClick)
    b.sigClick()

    # Disconnecting all signals
    print
    print "should see no messages"
    b.sigClick.disconnect_all()
    b.sigClick()

    # connecting multiple functions to a signal
    print
    print "should see two messages"
    l2 = Listener()
    b.sigClick.connect(l.onClick)
    b.sigClick.connect(l2.onClick)
    b.sigClick()
    
    # disconnecting individual functions
    print
    print "should see two messages"
    b.sigClick.disconnect(l.onClick)
    b.sigClick.connect(listenFunction)
    b.sigClick()
    
    # signals disconnecting automatically
    print
    print "should see one message"
    b.sigClick.disconnect_all()
    b.sigClick.connect(l.onClick)
    b.sigClick.connect(l2.onClick)
    del l2    
    b.sigClick()
    
    # example with arguments and a local signal
    print
    print "should see one message"
    sig = Signal()
    sig.connect(listenWithArgs)
    sig("Hello, World!")
    sig.disconnect(listenWithArgs)
    
    # disconnecting a signal by its WeakMethod object
    print
    print "should see one message"
    l3 = Listener()
    cb = b.sigClick.connect(l3.onClick)
    b.sigClick
    cb.disconnect()
    b.sigClick()

