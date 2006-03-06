
""" Re-implementation of Signals. """

import weakref
import inspect

import logging
logger = logging.getLogger('Lib.Events')


class AnonymousReceiver:
    pass
class EventError(Exception):
    pass


class Callback:   
    def __init__(self, cb, *args, **kwargs):
        
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



class Event:
    def __init__(self, owner):
        self.owner = weakref.ref(owner)
        self.callbacks = []

    def connect(self, func, *args, **kwargs):
        cb = Callback(func, *args, **kwargs)
        self.callbacks.append(cb)
        return cb
    
    def disconnect(self, cblist):
        if not isinstance(cblist, (list,tuple)):
            cblist = [cblist]

        for cb in cblist:
            try:
                self.callbacks.remove(cb)
            except ValueError, msg:
                logger.debug("Could not remove cb %s: %s" % (cb, msg))

    def disconnect_all(self):
        self.disconnect(self.callbacks[:])

    def trigger(self, *args, **kwargs):
        
        """ Trigger an event by calling all callbacks connected to it.

        The signature of the callback is

          def callback(sender, *args, **kwargs)
                       
        Where *args contains first all arguments specified to
        'trigger', and then all arguments specifed in the definition
        of the Event, The keyword arguments **kwargs contain all
        keyword arguments (both from trigger and from the Event).

        Any invalid callbacks (receiver does not exist anymore) are
        removed at the end of the trigger.
        """
        
        deprecated = []
        for cb in self.callbacks:
            all_args = args + cb.args
            all_kwargs = kwargs.copy()
            all_kwargs.update(cb.kwargs)

            # returns None if referenced object does not exist anymore
            receiver = cb.receiver()
            if receiver is None:
                logger.debug("emit: receiver for event is gone. callback marked for deletion.")
                deprecated.append(cb)
                continue

            owner = self.owner()
            if owner is None:
                raise EventError("emit: owner for event is gone. event trigger cancelled.")                
            
            try:
                if receiver == AnonymousReceiver:
                    cb.func(owner, *all_args, **all_kwargs)
                else:
                    cb.func(receiver, owner, *all_args, **all_kwargs)
            except:
                print ("Caught exception while trying to call callback [%s,%s,%s] during trigger of event '%s'." %
                                  (object.__str__(receiver), all_args, all_kwargs, self))
                raise

        # remove all obsolete callbacks
        for cb in deprecated:
            self.callbacks.remove(cb)            

    emit = trigger





def test():
    class TestClass:
        def __init__(self):
            self._events = {}
            self._events['notify'] = Event(self)
            
        def on_notify(self, sender, value):
            print "Class Receiver received value %s" % value

            
    def receiver(sender, value):
        print "Signal with value %s" % value                
        
    tc = TestClass()
    event = tc._events['notify']
    cb = event.connect(receiver)
    event.trigger(10)
    event.disconnect(cb)
    event.trigger(11)

    tc2 = TestClass()
    cb = event.connect(tc2.on_notify)
    event.trigger(12)
    
    del tc2
    event.trigger(13)
    raise SystemExit

    
if __name__ == "__main__":
    test()
    
