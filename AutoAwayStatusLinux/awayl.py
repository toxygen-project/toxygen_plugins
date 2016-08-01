import plugin_super_class
import threading
import time
from PySide import QtCore, QtGui
from subprocess import check_output
import json


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


class AutoAwayStatusLinux(plugin_super_class.PluginSuperClass):

    def __init__(self, *args):
        super().__init__('AutoAwayStatusLinux', 'awayl', *args)
        self._thread = None
        self._exec = None
        self._active = False
        self._time = json.loads(self.load_settings())['time']

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

    def change_status(self):
        invoke_in_main_thread(self._profile.set_status, 1)

    def get_window(self):
        inst = self

        class Window(QtGui.QWidget):
            def __init__(self):
                super(Window, self).__init__()
                self.setGeometry(QtCore.QRect(450, 300, 350, 100))
                self.label = QtGui.QLabel(self)
                self.label.setGeometry(QtCore.QRect(20, 0, 310, 35))
                self.label.setText(QtGui.QApplication.translate("AutoAwayStatusWindows", "Auto away time in minutes\n(0 - to disable)", None, QtGui.QApplication.UnicodeUTF8))
                self.time = QtGui.QLineEdit(self)
                self.time.setGeometry(QtCore.QRect(20, 40, 310, 25))
                self.time.setText(str(inst._time))
                self.setWindowTitle("AutoAwayStatusWindows")
                self.ok = QtGui.QPushButton(self)
                self.ok.setGeometry(QtCore.QRect(20, 70, 310, 25))
                self.ok.setText(
                    QtGui.QApplication.translate("AutoAwayStatusWindows", "Save", None, QtGui.QApplication.UnicodeUTF8))
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
            time.sleep(30)
            d = check_output(['xprintidle'])
            d = int(d) // 1000
            if self._time and d > 60 * self._time:
                self.change_status()
