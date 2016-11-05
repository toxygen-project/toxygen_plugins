import plugin_super_class


class uToxInlineSending(plugin_super_class.PluginSuperClass):

    def __init__(self, *args):
        super(uToxInlineSending, self).__init__('uToxInlineSending', 'uin', *args)
        self._tmp = None

    def stop(self):
        self._profile.send_screenshot = self._tmp

    def start(self):
        self._tmp = self._profile.send_screenshot

        def func(data):
            self._profile.send_inline(data, 'utox-inline.png')

        self._profile.send_screenshot = func
