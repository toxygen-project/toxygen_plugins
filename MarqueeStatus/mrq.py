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


class MarqueeStatus(plugin_super_class.PluginSuperClass):

    def __init__(self, *args):
        super(MarqueeStatus, self).__init__('MarqueeStatus', 'mrq', *args)
        self._thread = None
        self._exec = None
        self.active = False
        self.left = True

    def close(self):
        self.stop()

    def stop(self):
        self._exec = False
        if self.active:
            self._thread.join()

    def start(self):
        self._exec = True
        self._thread = threading.Thread(target=self.change_status)
        self._thread.start()

    def command(self, command):
        if command == 'rev':
            self.left = not self.left
        else:
            super(MarqueeStatus, self).command(command)

    def set_status_message(self):
        message = self._profile.status_message
        if self.left:
            self._profile.set_status_message(bytes(message[1:] + message[0], 'utf-8'))
        else:
            self._profile.set_status_message(bytes(message[-1] + message[:-1], 'utf-8'))

    def init_status(self):
        self._profile.status_message = bytes(self._profile.status_message.strip() + '   ', 'utf-8')

    def change_status(self):
        self.active = True
        tmp = self._profile.status_message
        time.sleep(10)
        invoke_in_main_thread(self.init_status)
        while self._exec:
            time.sleep(1)
            if self._profile.status is not None:
                invoke_in_main_thread(self.set_status_message)
        invoke_in_main_thread(self._profile.set_status_message, bytes(tmp, 'utf-8'))
        self.active = False
