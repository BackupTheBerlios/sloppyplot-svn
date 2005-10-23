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


# register signal => new entry in self._signals
# connect signal => new entry in self._slots
# maybe write a class CallbackManager, that has signals and slots
# and has methods 'connect', 'disconnect' and so on.  It would
# have to know the sender, of course.


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


    
class HasSignals:

    def __init__(self):
        self._signals = [] # list of Signal objects
        self._slots = {} # 


    def connect_signal(self, signal_name, callback, *args, **kwargs):
        new_signal = Signal(sender, signal_name, callback, *args, **kwargs)
        self._signals.append(new_signal)
        return newSignal

    def disconnect_signal(self, signal=None, signal_name=None, receiver=None):
        """ Disconnect all signals matching the given criteria. """
        if signal is not None:
            signals = [signal]
        else:
            signals = self.get_signals(receiver=receiver, signal_name=signal_name)

        for signal in signals:
            try:
                self._signals.remove(signal)
            except ValueError:
                logger.error("disconnect_signal: signal not found!")

    def disconnect_signals(self, signal_list):
        """ Disconnect all given signals. """
        while len(signals) > 0:
            self.disconnect_signal(signal_list.pop(0))

    def emit_signal(self, signal_name, *args, **kwargs):
        pass

    def get_signals(self, receiver=None, signal_name=None):
        """ Return all signals that match the given criteria. """
        signals = self.signals
        if receiver is not None:
            signals = [signal for signal in signals if id(signal.receiver()) == id(receiver)]
        if signal_name is not None:
            signals = [signal for signal in signals if id(signal.name) == id(signal_name)]
        return signals                       
        
                                       
                                       
    
