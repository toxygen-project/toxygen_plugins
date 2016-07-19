import plugin_super_class
from PySide import QtGui, QtCore


class SearchPlugin(plugin_super_class.PluginSuperClass):

    def __init__(self, *args):
        super(SearchPlugin, self).__init__('SearchPlugin', 'srch', *args)

    def get_message_menu(self, menu, text):
        google = QtGui.QAction(
            QtGui.QApplication.translate("srch", "Find in Google", None, QtGui.QApplication.UnicodeUTF8),
            menu)
        google.triggered.connect(lambda: self.google(text))

        duck = QtGui.QAction(
            QtGui.QApplication.translate("srch", "Find in DuckDuckGo", None, QtGui.QApplication.UnicodeUTF8),
            menu)
        duck.triggered.connect(lambda: self.duck(text))

        yandex = QtGui.QAction(
            QtGui.QApplication.translate("srch", "Find in Yandex", None, QtGui.QApplication.UnicodeUTF8),
            menu)
        yandex.triggered.connect(lambda: self.yandex(text))

        bing = QtGui.QAction(
            QtGui.QApplication.translate("srch", "Find in Bing", None, QtGui.QApplication.UnicodeUTF8),
            menu)
        bing.triggered.connect(lambda: self.bing(text))

        return [duck, google, yandex, bing]

    def google(self, text):
        url = QtCore.QUrl('https://www.google.com/search?q=' + text)
        QtGui.QDesktopServices.openUrl(url)

    def duck(self, text):
        url = QtCore.QUrl('https://duckduckgo.com/?q=' + text)
        QtGui.QDesktopServices.openUrl(url)

    def yandex(self, text):
        url = QtCore.QUrl('https://yandex.com/search/?text=' + text)
        QtGui.QDesktopServices.openUrl(url)

    def bing(self, text):
        url = QtCore.QUrl('https://www.bing.com/search?q=' + text)
        QtGui.QDesktopServices.openUrl(url)
