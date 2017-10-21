import plugin_super_class
from PyQt5 import QtGui, QtWidgets
import json


class AutoAnswer(plugin_super_class.PluginSuperClass):

    def __init__(self, *args):
        super(AutoAnswer, self).__init__('AutoAnswer', 'aans', *args)
        self._data = json.loads(self.load_settings())
        self._tmp = None

    def get_description(self):
        return QtWidgets.QApplication.translate("aans", 'Plugin which allows you to auto answer on calls.')

    def start(self):
        self._tmp = self._profile.incoming_call

        def func(audio, video, friend_number):
            if self._profile.get_friend_by_number(friend_number).tox_id in self._data['id']:
                self._profile.accept_call(friend_number, audio, video)
            else:
                self._tmp(friend_number, audio, video)

        self._profile.incoming_call = func

    def stop(self):
        self._profile.incoming_call = self._tmp

    def get_menu(self, menu, num):
        friend = self._profile.get_friend(num)
        if friend.tox_id in self._data['id']:
            text = 'Disallow auto answer'
        else:
            text = 'Allow auto answer'
        act = QtWidgets.QAction(QtWidgets.QApplication.translate("aans", text), menu)
        act.triggered.connect(lambda: self.toggle(friend.tox_id))
        return [act]

    def toggle(self, tox_id):
        if tox_id in self._data['id']:
            self._data['id'].remove(tox_id)
        else:
            self._data['id'].append(tox_id)
        self.save_settings(json.dumps(self._data))
