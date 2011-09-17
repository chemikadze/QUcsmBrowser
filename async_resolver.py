#!/usr/bin/python

from PySide import QtCore
from PySide.QtCore import SIGNAL
from PySide.QtCore import QThread
from PySide.QtCore import QMutex, QSemaphore

from pyucsm import UcsmError

MAX_QUEUE_LEN = 100

class AsyncResolver(QThread):

    object_resolved = QtCore.Signal('object_resolved(QVariant)')

    def __init__(self):
        super(AsyncResolver, self).__init__()
        self._task_queue = []
        self._mutex = QMutex()
        self._semaphore = QSemaphore()
        self.working = False

    def synchronized(f):
        def wrap(self, *args, **kwargs):
            self._mutex.lock()
            try:
                return f(self, *args, **kwargs)
            finally:
                self._mutex.unlock()
        return wrap

    def add_task(self, dn):
        self._task_queue.append(dn)
        #print self._semaphore.available()
        self._semaphore.release()
        #print 'before release'

    @synchronized
    def _append_task(self, task):
        self._task_queue.append(task)

    @synchronized
    def _pop_task(self, task):
        return self._task_queue.pop()

    def consume_task(self):
        #print self._semaphore.available()
        self._semaphore.acquire()
        #print 'after acq'
        obj = self._task_queue.pop()
        return obj

    def stop_work(self):
        self.working = False
        if self._task_queue:
            self._append_task(None)
        self._semaphore.release()

    @synchronized
    def _do_task(self, task):
        return task()

    def run(self):
        self.working = True
        while self.working:
            task = self.consume_task()
            if task:
                try:
                    obj = self._do_task(task)
                except UcsmError:
                    pass
                else:
                    self.emit(SIGNAL('object_resolved(QVariant)'), obj)
            else:
                break