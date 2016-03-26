from kivy.uix.gridlayout import GridLayout
from ui.remotekey import RemoteKey
from kivy.logger import Logger

class KeyGrid(GridLayout):

    def get_key_button(self, button_id):
        if button_id in self.ids:
            return self.ids[button_id]

    def _set_child_property(self, child_id, prop_name, value):
        #if child_id in self.ids:
        if isinstance(child_id, RemoteKey):
            child_id.__setattr__(prop_name, value)

    def set_all_child_property(self, prop_name, value):
        #Logger.info('KEYGROUP-{}: applying {} = {} for all'.format(self.id, prop_name, value))
        for child_id in self.children:
            self._set_child_property(child_id, prop_name, value)

    def change_remote_node_all(self, remote_node):
        self.set_all_child_property('remote_node', remote_node)

    def change_remote_name_all(self, remote_name):
        self.set_all_child_property('remote_name', remote_name)

    def change_key_name(self, child_id, key_name):
        self._set_child_property(child_id, 'key_name', key_name)

    def disable_all(self):
        self.set_all_child_property('disabled', True)

    def disable_child(self, child_id):
        if child_id in self.ids:
            self.ids[child_id].disabled = True

    def enable_child(self, child_id):
        if child_id in self.ids:
            self.ids[child_id].disabled = False
