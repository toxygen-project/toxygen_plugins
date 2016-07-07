import plugin_super_class
from PySide import QtCore
import time


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


class Bot(plugin_super_class.PluginSuperClass):

    def __init__(self, *args):
        super(Bot, self).__init__('Bot', 'bot', *args)
        self._callback = None
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.initialize)

    def start(self):
        self._timer.start(10000)

    def initialize(self):
        self._timer.stop()
        self._callback = self._tox.friend_message_cb

        def incoming_message(tox, friend_number, message_type, message, size, user_data):
            self._callback(tox, friend_number, message_type, message, size, user_data)
            if self._profile.status == 1:
                self.answer(friend_number, str(message, 'utf-8'))

        self._tox.callback_friend_message(incoming_message, None)

    def stop(self):
        self._tox.callback_friend_message(self._callback, None)

    def close(self):
        self.stop()

    def answer(self, friend_number, message):
        invoke_in_main_thread(self._profile.send_message, message, friend_number)


