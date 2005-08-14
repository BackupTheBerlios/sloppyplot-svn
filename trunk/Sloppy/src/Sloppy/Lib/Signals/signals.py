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


import weakref

import logging
logger = logging.getLogger('Base.signals')
logger.setLevel(logging.WARN)



class __Anonymous:  pass
Anonymous = __Anonymous()


class Signal:

    def __init__(self, sender, name, callback, *args, **kwargs):
        logger.debug("new signal...")
        self.sender = sender
        self.name = name

        # Signal.receiver is a weak reference to the receiving object.
        # The user should not explicitly provide this object, so
        # we need to extract this information from the given callback.
        # We perform this separation of object and unbound method via
        # the methods im_self and im_func. If `callback` is only
        # a method, not a method bound to an object, then an
        # AttributeError is raised, caught and the receiver is set to
        # the so called Anonymous receiver.
        try:
            # Try bound method.
            # If unbound, an AttributeError will occur
            receiver = callback.im_self
            callback = callback.im_func
            logger.debug("(bound to object)")
        except AttributeError:
            # unbound method
            receiver = Anonymous
            callback = callback
            logger.debug("(unbound)")

        self.callback = callback
        self.receiver = weakref.ref(receiver)
        
        self.args = args
        self.kwargs = kwargs


class __Emitter:

    def __init__(self):
        self.signals = list()

    def connect(self, sender, name, callback, *args, **kwargs):
        new_signal = Signal(sender, name, callback, *args, **kwargs)        
        self.signals.append( new_signal )
        return new_signal

    def disconnect(self, signal=None, sender=None, receiver=None, name=None):
        if signal is not None:
            signals = [signal]
        else:
            signals = self.get_signals(sender=sender, receiver=receiver, name=name)

        for signal in signals:
            try:            
                self.signals.remove(signal)
            except ValueError:
                logger.debug("disconnect: signal not found.")

    def disconnect_list(self, signals):
        while len(signals) > 0:            
            self.disconnect(signals.pop(0))
    
    def emit(self, sender, name, *args, **kwargs):

        logger.debug("emit: received emission of signal '%s'" % name)
        signals = [signal for signal in self.signals
                   if id(signal.sender) == id(sender) \
                   and signal.name == name ]
        logger.debug("emit: There are %d possible signals." % len(signals))

        deprecated = list()
        n = 1
        for signal in signals:
            logger.debug("emit: Signal #%d" % n) ; n+=1
            all_args = signal.args + args
            all_kwargs = kwargs.copy()
            all_kwargs.update( signal.kwargs )

            # returns None if referenced object does not exist anymore
            receiver = signal.receiver()
            
            if receiver is None:
                logger.debug("emit: receiver for signal is gone. signal marked for deletion.")
                deprecated.append(signal)
                continue

            try:
                if receiver == Anonymous:
                    logger.debug("(anonymous signal)")
                    signal.callback( sender, *all_args, **all_kwargs )
                else:
                    logger.debug("(regular signal!)")
                    signal.callback( receiver, sender, *all_args, **all_kwargs )
            except:
                print "Caught exception while trying to call signal callback", \
                      receiver, sender, all_args, all_kwargs
                raise

        # remove all obsolete signals
        for signal in deprecated:
            logger.debug("emit: -- removing signal --")
            self.signals.remove(signal)


    def list_signals(signals):
        print "Listing signals:"        
        for signal in signals:
            print "  Sender: %s, Name: %s, Receiver: %s, Args: %s, Kwargs: %s" % \
                      (signal.sender, signal.name, signal.receiver(), signal.args, signal.kwargs)
    list_signals = staticmethod(list_signals)


    def get_signals(self, receiver=None, sender=None, name=None):
        signals = self.signals
        if receiver is not None:
            signals = [signal for signal in signals if id(signal.receiver()) == id(receiver)]
        if sender is not None:
            signals = [signal for signal in signals if id(signal.sender) == id(sender)]
        if name is not None:
            signals = [signal for signal in signals if id(signal.name) == id(name)]
        return signals

###############################################################################


__emitter_instance = __Emitter()

emit = __emitter_instance.emit
connect = __emitter_instance.connect
disconnect = __emitter_instance.disconnect
disconnect_list = __emitter_instance.disconnect_list
list_signals = __emitter_instance.list_signals
get_signals = __emitter_instance.get_signals


def test():
    class MyDoc:
        def set_value(self,newval):
            print "[EMITTING]"
            self.value = newval
            emit(self, 'value', value=newval)

    class TestReceiver:
        def test(self,doc,value):
            print "-> TestReceiver: document's new value is %d" % value
    
    def anonymous_receiver(doc,value):
        print "-> anonymous receiver: document's new value is %d" % value
      
    doc = MyDoc()
    tr = TestReceiver()
    cb = tr.test

    print """
    We will register two signals.
    One is bound to the object `TestReceiver`,
    while the other is bound to the function `anonymous_receiver`.
    """
    connect(sender=doc, name='value', callback=tr.test)

    # anonymous receiver
    my_signal = connect(sender=doc, name='value', callback=anonymous_receiver)

    print """
    As you can see next, the signals are properly set up.
    Each time you see [EMITTING], we will change the document`s
    value to 42.  The document should then emit a 'value' signal
    to all registered callbacks.  The receivers will then
    print messages beginning with '->'.
    """
    doc.set_value(42)
    print """
    Now I remove the callback!
    Nothing should change, since the object is still there.
    """
    cb=None
    doc.set_value(42)
    print """
    Now I remove the object itself!
    This time, only the anonymous callback should be called
    while the object callback should be removed.
    """
    tr = None
    doc.set_value(42)

    print """
    Now we disconnect the anonymous signal through `disconnect`
    and we should get no signal at all after emission.
    """
    disconnect(my_signal)
    doc.set_value(42)

    print """
    Now we try to disconnect the same signal again.
    Let's see what happens...
    """
    disconnect(my_signal)


    doc = MyDoc()
    def whatever(self,sender): pass
    connect(doc, name='value', callback=whatever)
    connect(doc, name='value', callback=whatever)
    list_all()
    list_by_sender(doc)
    disconnect_by_sender(doc)
    list_all()


if __name__ == "__main__":
    test()
