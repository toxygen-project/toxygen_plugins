import plugin_super_class
import threading
import time
from PyQt5 import QtCore


class InvokeEvent(QtCore.QEvent):
    EVENT_TYPE = QtCore.QEvent.Type(QtCore.QEvent.registerEventType())

    def __init__(self, fn, *args, **kwargs):
        QtCore.QEvent.__init__(self, InvokeEvent.EVENT_TYPE)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs


class Invoker(QtCore.QObject):

    def event(self, event):
        event.fn(*event.args, **event.kwargs)
        return True

_invoker = Invoker()


def invoke_in_main_thread(fn, *args, **kwargs):
    QtCore.QCoreApplication.postEvent(_invoker, InvokeEvent(fn, *args, **kwargs))


class Garland(plugin_super_class.PluginSuperClass):

    def __init__(self, *args):
        super(Garland, self).__init__('Garland', 'grlnd', *args)
        self._thread = None
        self._exec = None
        self._time = 3

    def close(self):
        self.stop()

    def stop(self):
        self._exec = False
        self._thread.join()

    def start(self):
        self._exec = True
        self._thread = threading.Thread(target=self.change_status)
        self._thread.start()

    def command(self, command):
        if command.startswith('time'):
            self._time = max(int(command.split(' ')[1]), 300) / 1000
        else:
            super().command(command)

    def update(self):
        self._profile.set_status((self._profile.status + 1) % 3)

    def change_status(self):
        time.sleep(5)
        while self._exec:
            invoke_in_main_thread(self.update)
            time.sleep(self._time)
