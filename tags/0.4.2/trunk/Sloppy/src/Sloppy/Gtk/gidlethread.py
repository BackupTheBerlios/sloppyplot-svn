#
# This module is taken from the ActiveState Programmer Network and
# is (C)opyright 2004 by Arjan Molenaar.
#

"""This module contains some helpers that can be used to execute generator
functions in the GObject main loop.

This module provided the following classes:
GIdleThread - Thread like behavior for generators in a main loop
Queue - A simple queue implementation suitable for use with GIdleThread

Exceptions:
QueueEmpty - raised when one tried to get a value of an empty queue
QueueFull - raised when the queue reaches it's max size and the oldest item
            may not be disposed.
"""

from __future__ import generators

import gobject
import time
import traceback

class GIdleThread(object):
    """This is a pseudo-"thread" for use with the GTK+ main loop.

    This class does act a bit like a thread, all code is executed in
    the callers thread though. The provided function should be a generator
    (or iterator).

    It can be started with start(). While the "thread" is running is_alive()
    can be called to see if it's alive. wait([timeout]) will wait till the
    generator is finished, or timeout seconds.
    
    If an exception is raised from within the generator, it is stored in
    the error property. Execution of the generator is finished.

    Note that this routine runs in the current thread, so there is no need
    for nasty locking schemes.

    Example (runs a counter through the GLib main loop routine):
    >>> def counter(max): for x in xrange(max): yield x
    >>> t = GIdleThread(counter(123))
    >>> t.start()
    >>> while gen.is_alive():
    ...     main.iteration(False)
    """

    def __init__(self, generator, queue=None):
        assert hasattr(generator, 'next'), 'The generator should be an iterator'
        self._generator = generator
        self._queue = queue
        self._idle_id = 0
        self._error = None

    def start(self, priority=gobject.PRIORITY_LOW):
        """Start the generator. Default priority is low, so screen updates
        will be allowed to happen.
        """
        idle_id = gobject.idle_add(self.__generator_executer,
                                   priority=priority)
        self._idle_id = idle_id
        return idle_id

    def wait(self, timeout=0):
        """Wait until the corouine is finished or return after timeout seconds.
        This is achieved by running the GTK+ main loop.
        """
        clock = time.clock
        start_time = clock()
        main = gobject.main_context_default()
        while self.is_alive():
            main.iteration(False)
            if timeout and (clock() - start_time >= timeout):
                return

    def interrupt(self):
        """Force the generator to stop running.
        """
        if self.is_alive():
            gobject.source_remove(self._idle_id)
            self._idle_id = 0

    def is_alive(self):
        """Returns True if the generator is still running.
        """
        return self._idle_id != 0

    error = property(lambda self: self._error,
                     doc="Return a possible exception that had occured "\
                         "during execution of the generator")

    def __generator_executer(self):
        try:
            result = self._generator.next()
            if self._queue:
                try:
                    print "Putting", self._queue
                    self._queue.put(result)
                except QueueFull:
                    self.wait(0.5)
                    # If this doesn't work...
                    self._queue.put(result)
            return True
        except StopIteration:
            self._idle_id = 0
            return False
        except Exception, e:
            self._error = e
            traceback.print_exc()
            self._idle_id = 0
            return False


class QueueEmpty(Exception):
    """Exception raised whenever the queue is empty and someone tries to fetch
    a value.
    """
    pass


class QueueFull(Exception):
    """Exception raised when the queue is full and the oldest item may not be
    disposed.
    """
    pass


class Queue(object):
    """A FIFO queue. If the queue has a max size, the oldest item on the
    queue is dropped if that size id exceeded.
    """

    def __init__(self, size=0, dispose_oldest=True):
        self._queue = []
        self._size = size
        self._dispose_oldest = dispose_oldest

    def put(self, item):
        """Put item on the queue. If the queue size is limited ...
        """
        if self._size > 0 and len(self._queue) >= self._size:
            if self._dispose_oldest:
                self.get()
            else:
                raise QueueFull

        self._queue.insert(0, item)

    def get(self):
        """Get the oldest item off the queue.
        QueueEmpty is raised if no items are left on the queue.
        """
        try:
            return self._queue.pop()
        except IndexError:
            raise QueueEmpty



def test():
    def counter(max):
        for i in range(max):
            yield i

    def shower(queue):
        # Never stop reading the queue:
        while True:
            try:
                cnt = queue.get()
                print 'cnt =', cnt
            except QueueEmpty:
                pass
            yield None

    print 'Test 1: (should print range 0..22)'
    queue = Queue()
    c = GIdleThread(counter(23), queue)
    s = GIdleThread(shower(queue))
    
    main = gobject.main_context_default()
    c.start()
    s.start()
    s.wait(2)

    print 'Test 2: (should only print 22)'
    queue = Queue(size=1)
    c = GIdleThread(counter(23), queue)
    s = GIdleThread(shower(queue))
    
    main = gobject.main_context_default()
    c.start(priority=gobject.PRIORITY_DEFAULT)
    s.start()
    s.wait(3)



import gtk
    
def mytest():

    win = gtk.Window()
    win.connect("destroy", gtk.main_quit)
    win.show()

    pb = gtk.ProgressBar()
    pb.set_text("Sample ProgressBar")
    pb.set_pulse_step(0.05)
    pb.show()
    win.add(pb)

    def do_import():
        filelist = ['a','b','c','d']
        n = 0
        for file in filelist:
            yield ("Working on file %s" % file, None)
            #...do something here...
            time.sleep(1)
            if n == 3:
                raise RuntimeError("Sample Exception")
            n += 1
            fraction = float(n)/len(filelist)
            yield (None, fraction)
            
    def set_text(queue):
        while True:
            try:
                filename, fraction = queue.get()
                if filename is not None:
                    pb.set_text(filename)
                if fraction is not None:
                    pb.set_fraction(fraction)
            except QueueEmpty:
                pass
            yield None

    queue = Queue()
    s = GIdleThread(set_text(queue))
    s.start()

    c = GIdleThread(do_import(), queue)
    c.start()
    c.wait(2)

    gtk.main()

if __name__ == '__main__':
    mytest()
