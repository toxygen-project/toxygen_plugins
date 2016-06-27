import plugin_super_class
from PySide import QtGui, QtCore
import json


class CopyableToxId(plugin_super_class.PluginSuperClass):

    def __init__(self, *args):
        super(CopyableToxId, self).__init__('CopyableToxId', 'toxid', *args)
        self._data = json.loads(self.load_settings())
        self._copy = False
        self._curr = -1
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(lambda: self.timer())
        self.load_translator()

    def get_description(self):
        return QtGui.QApplication.translate("TOXID", 'Plugin which allows you to copy TOX ID of your friend easily.', None, QtGui.QApplication.UnicodeUTF8)

    def get_window(self):
        inst = self

        class Window(QtGui.QWidget):

            def __init__(self):
                super(Window, self).__init__()
                self.setGeometry(QtCore.QRect(450, 300, 350, 100))
                self.send = QtGui.QCheckBox(self)
                self.send.setGeometry(QtCore.QRect(20, 10, 310, 25))
                self.send.setText(QtGui.QApplication.translate("TOXID", "Send my TOX ID to contacts", None, QtGui.QApplication.UnicodeUTF8))
                self.setWindowTitle(QtGui.QApplication.translate("TOXID", "CopyableToxID", None, QtGui.QApplication.UnicodeUTF8))
                self.send.clicked.connect(self.update)
                self.send.setChecked(inst._data['send_id'])
                self.help = QtGui.QPushButton(self)
                self.help.setGeometry(QtCore.QRect(20, 40, 200, 25))
                self.help.setText(QtGui.QApplication.translate("TOXID", "List of commands", None, QtGui.QApplication.UnicodeUTF8))
                self.help.clicked.connect(lambda: inst.command('help'))

            def update(self):
                inst._data['send_id'] = self.send.isChecked()
                inst.save_settings(json.dumps(inst._data))

        return Window()

    def lossless_packet(self, data, friend_number):
        if len(data):
            self._data['id'] = list(filter(lambda x: not x.startswith(data[:64]), self._data['id']))
            self._data['id'].append(data)
            if self._copy:
                self._timer.stop()
                self._copy = False
                clipboard = QtGui.QApplication.clipboard()
                clipboard.setText(data)
            self.save_settings(json.dumps(self._data))
        elif self._data['send_id']:
            self.send_lossless(self._tox.self_get_address(), friend_number)

    def error(self):
        msgbox = QtGui.QMessageBox()
        title = QtGui.QApplication.translate("TOXID", "Error", None, QtGui.QApplication.UnicodeUTF8)
        msgbox.setWindowTitle(title.format(self._name))
        text = QtGui.QApplication.translate("TOXID", "Tox ID cannot be copied", None, QtGui.QApplication.UnicodeUTF8)
        msgbox.setText(text)
        msgbox.exec_()

    def timer(self):
        self._copy = False
        if self._curr + 1:
            public_key = self._tox.friend_get_public_key(self._curr)
            self._curr = -1
            arr = list(filter(lambda x: x.startswith(public_key), self._data['id']))
            if len(arr):
                clipboard = QtGui.QApplication.clipboard()
                clipboard.setText(arr[0])
            else:
                self.error()
        else:
            self.error()
        self._timer.stop()

    def friend_connected(self, friend_number):
        self.send_lossless('', friend_number)

    def command(self, text):
        if text == 'copy':
            num = self._profile.get_active_number()
            if num == -1:
                return
        elif text.startswith('copy '):
            num = int(text[5:])
            if num < 0:
                return
        elif text == 'enable':
            self._copy = True
            return
        elif text == 'disable':
            self._copy = False
            return
        elif text == 'help':
            msgbox = QtGui.QMessageBox()
            title = QtGui.QApplication.translate("TOXID", "List of commands for plugin CopyableToxID", None, QtGui.QApplication.UnicodeUTF8)
            msgbox.setWindowTitle(title)
            text = QtGui.QApplication.translate("TOXID", """Commands:
copy: copy TOX ID of current friend
copy <friend_number>: copy TOX ID of friend with specified number
enable: allow send your TOX ID to friends
disable: disallow send your TOX ID to friends
help: show this help""", None, QtGui.QApplication.UnicodeUTF8)
            msgbox.setText(text)
            msgbox.exec_()
            return
        else:
            return
        public_key = self._tox.friend_get_public_key(num)
        arr = list(filter(lambda x: x.startswith(public_key), self._data['id']))
        if self._profile.get_friend_by_number(num).status is None and len(arr):
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setText(arr[0])
        elif self._profile.get_friend_by_number(num).status is not None:
            self._copy = True
            self._curr = num
            self.send_lossless('', num)
            self._timer.start(2000)
        else:
            self.error()

    def get_menu(self, menu, num):
        act = QtGui.QAction(QtGui.QApplication.translate("TOXID", "Copy TOX ID", None, QtGui.QApplication.UnicodeUTF8), menu)
        friend = self._profile.get_friend(num)
        act.connect(act, QtCore.SIGNAL("triggered()"), lambda: self.command('copy ' + str(friend.number)))
        return [act]
