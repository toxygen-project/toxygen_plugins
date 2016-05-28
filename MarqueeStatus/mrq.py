import plugin_super_class
import threading
import time
from PySide import QtCore


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
        self._thread = threading.Thread(target=self.change_status)
        self._exec = None
        self.active = False

    def close(self):
        self.stop()

    def stop(self):
        self._exec = False
        if self.active:
            self._thread.join()

    def start(self):
        self._exec = True
        self._thread.start()

    def set_status_message(self):
        self._profile.status_message = self._profile.status_message[1:] + self._profile.status_message[0]

    def init_status(self):
        self._profile.status_message = self._profile.status_message.strip() + '   '

    def change_status(self):
        self.active = True
        tmp = self._profile.status_message
        time.sleep(10)
        invoke_in_main_thread(self.init_status)
        while self._exec:
            time.sleep(1)
            if self._profile.status is not None:
                invoke_in_main_thread(self.set_status_message)
        invoke_in_main_thread(self._profile.set_status_message, tmp)
        self.active = False
