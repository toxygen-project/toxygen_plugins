import plugin_super_class
import threading
import time
from PyQt5 import QtCore, QtWidgets
from ctypes import Structure, windll, c_uint, sizeof, byref
import json


class LASTINPUTINFO(Structure):
    _fields_ = [('cbSize', c_uint), ('dwTime', c_uint)]


def get_idle_duration():
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = sizeof(lastInputInfo)
    windll.user32.GetLastInputInfo(byref(lastInputInfo))
    millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
    return millis / 1000.0


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


class AutoAwayStatusWindows(plugin_super_class.PluginSuperClass):

    def __init__(self, *args):
        super().__init__('AutoAwayStatusWindows', 'awayw', *args)
        self._thread = None
        self._exec = None
        self._active = False
        self._time = json.loads(self.load_settings())['time']
        self._prev_status = 0

    def close(self):
        self.stop()

    def stop(self):
        self._exec = False
        if self._active:
            self._thread.join()

    def start(self):
        self._exec = True
        self._thread = threading.Thread(target=self.loop)
        self._thread.start()

    def save(self):
        self.save_settings('{"time": ' + str(self._time) + '}')

    def change_status(self, status=1):
        if self._profile.status != 1:
            self._prev_status = self._profile.status
        invoke_in_main_thread(self._profile.set_status, status)

    def get_window(self):
        inst = self

        class Window(QtWidgets.QWidget):
            def __init__(self):
                super(Window, self).__init__()
                self.setGeometry(QtCore.QRect(450, 300, 350, 100))
                self.label = QtWidgets.QLabel(self)
                self.label.setGeometry(QtCore.QRect(20, 0, 310, 35))
                self.label.setText(QtWidgets.QApplication.translate("AutoAwayStatusWindows", "Auto away time in minutes\n(0 - to disable)"))
                self.time = QtWidgets.QLineEdit(self)
                self.time.setGeometry(QtCore.QRect(20, 40, 310, 25))
                self.time.setText(str(inst._time))
                self.setWindowTitle("AutoAwayStatusWindows")
                self.ok = QtWidgets.QPushButton(self)
                self.ok.setGeometry(QtCore.QRect(20, 70, 310, 25))
                self.ok.setText(
                    QtWidgets.QApplication.translate("AutoAwayStatusWindows", "Save"))
                self.ok.clicked.connect(self.update)

            def update(self):
                try:
                    t = int(self.time.text())
                except:
                    t = 0
                inst._time = t
                inst.save()
                self.close()

        return Window()

    def loop(self):
        self._active = True
        while self._exec:
            time.sleep(5)
            d = get_idle_duration()
            if self._time:
                if d > 60 * self._time:
                    self.change_status()
                elif self._profile.status == 1:
                    self.change_status(self._prev_status)
