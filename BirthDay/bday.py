import plugin_super_class
from PySide import QtGui, QtCore
import json
import importlib


class BirthDay(plugin_super_class.PluginSuperClass):

    def __init__(self, *args):
        super(BirthDay, self).__init__('BirthDay', 'bday', *args)
        self._data = json.loads(self.load_settings())
        self._datetime = importlib.import_module('datetime')
        self._timers = []

    def start(self):
        now = self._datetime.datetime.now()
        today = {}
        x = self._profile.tox_id[:64]
        for key in self._data:
            if key != x and key != 'send_date':
                arr = self._data[key].split('.')
                if int(arr[0]) == now.day and int(arr[1]) == now.month:
                    today[key] = now.year - int(arr[2])
        if len(today):
            msgbox = QtGui.QMessageBox()
            title = QtGui.QApplication.translate('BirthDay', "Birthday!", None,
                                                 QtGui.QApplication.UnicodeUTF8)
            msgbox.setWindowTitle(title)
            text = ', '.join(self._profile.get_friend_by_number(self._tox.friend_by_public_key(x)).name + ' ({})'.format(today[x]) for x in today)
            msgbox.setText('Birthdays: ' + text)
            msgbox.exec_()

    def get_window(self):
        inst = self
        x = self._profile.tox_id[:64]

        class Window(QtGui.QWidget):

            def __init__(self):
                super(Window, self).__init__()
                self.setGeometry(QtCore.QRect(450, 300, 350, 150))
                self.send = QtGui.QCheckBox(self)
                self.send.setGeometry(QtCore.QRect(20, 10, 310, 25))
                self.send.setText(QtGui.QApplication.translate('BirthDay', "Send my birthday date to contacts", None, QtGui.QApplication.UnicodeUTF8))
                self.setWindowTitle(QtGui.QApplication.translate('BirthDay', "Birthday", None, QtGui.QApplication.UnicodeUTF8))
                self.send.clicked.connect(self.update)
                self.send.setChecked(inst._data['send_date'])
                self.date = QtGui.QLineEdit(self)
                self.date.setGeometry(QtCore.QRect(20, 50, 310, 25))
                self.date.setPlaceholderText(QtGui.QApplication.translate('BirthDay', "Date in format dd.mm.yyyy", None, QtGui.QApplication.UnicodeUTF8))
                self.set_date = QtGui.QPushButton(self)
                self.set_date.setGeometry(QtCore.QRect(20, 90, 310, 25))
                self.set_date.setText(QtGui.QApplication.translate('BirthDay', "Save date", None, QtGui.QApplication.UnicodeUTF8))
                self.set_date.clicked.connect(self.save_curr_date)
                self.date.setText(inst._data[x] if x in inst._data else '')

            def save_curr_date(self):
                inst._data[x] = self.date.text()
                inst.save_settings(json.dumps(inst._data))
                self.close()

            def update(self):
                inst._data['send_date'] = self.send.isChecked()
                inst.save_settings(json.dumps(inst._data))

        return Window()

    def lossless_packet(self, data, friend_number):
        if len(data):
            friend = self._profile.get_friend_by_number(friend_number)
            self._data[friend.tox_id] = data
            self.save_settings(json.dumps(self._data))
        elif self._data['send_date'] and self._profile.tox_id[:64] in self._data:
            self.send_lossless(self._data[self._profile.tox_id[:64]], friend_number)

    def friend_connected(self, friend_number):
        timer = QtCore.QTimer()
        timer.timeout.connect(lambda: self.timer(friend_number))
        timer.start(10000)
        self._timers.append(timer)

    def timer(self, friend_number):
        timer = self._timers.pop()
        timer.stop()
        if self._profile.get_friend_by_number(friend_number).tox_id not in self._data:
            self.send_lossless('', friend_number)
