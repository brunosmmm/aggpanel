import json
import os
from userman.exception import *
from kivy.logger import Logger
import re
from collections import OrderedDict

USER_ACTION_LIST = ['send_remote_key']
JSON_FILE_REGEX = re.compile(r'.*\.json$')
KEY_GROUP_LIST = ['mediactrl_group', 'volctrl_group', 'numericctrl_group']

class UserAction(object):
    def __init__(self, description, action_list):
        self.desc = description
        self.action_list = action_list

    def get_action_list(self):
        return self.action_list

class ButtonScheme(object):
    def __init__(self, description, group_scheme):
        self.desc = description
        self.scheme = group_scheme

    def get_group_scheme(self):
        return self.scheme

class UserConfigManager(object):
    def __init__(self, config_path, action_hook_dict):
        self.config_path = config_path
        self.user_actions = {}
        self.button_schemes = {}
        self.action_hooks = dict(action_hook_dict)

        self._scan_files()

    def _scan_subfolder(self, path, discover_action):
        files = os.walk(path).next()[2]
        for fname in files:
            if JSON_FILE_REGEX.match(fname) != None:
                Logger.info('USERCFGMAN: discovered file {}'.format(fname))
                if discover_action(os.path.join(path, fname)) == False:
                    Logger.info('USERCFGMAN: failed to load {}'.format(fname))


    def _scan_files(self):
        folders = os.walk(self.config_path).next()[1]

        for folder in folders:
            if folder == 'actions':
                self._scan_subfolder(os.path.join(self.config_path, folder), self._load_action)
            if folder == 'schemes':
                self._scan_subfolder(os.path.join(self.config_path, folder), self._load_scheme)

    def register_action_hook(self, action_type, action_cb):
        self.action_hooks[action_type] = action_cb

    def _load_action(self, action_file):

        loaded = False
        with open(action_file, 'r') as f:
            act = json.load(f)
            self.user_actions[act['name']] = UserAction(act['description'],
                                                        act['actions'])
            loaded = True

        Logger.info('USERCFGMAN: loaded action "{}"'.format(act['name']))

        return loaded

    def _load_scheme(self, scheme_file):
        loaded = False

        with open(scheme_file, 'r') as f:
            scheme = json.load(f, object_pairs_hook=OrderedDict)
            self.button_schemes[scheme['name']] = ButtonScheme(scheme['description'],
                                                               scheme['scheme'])
            loaded = True

        Logger.info('USERCFGMAN: loaded scheme "{}"'.format(scheme['name']))

        return loaded

    def execute_action(self, action_name):
        if action_name not in self.user_actions:
            raise ActionNotAvailableError('requested action is not available')

        action_list = self.user_actions[action_name].get_action_list()
        for step in action_list:
            for act_type, act in step.iteritems():
                if act_type not in self.action_hooks:
                    raise ActionNotAvailableError('requested action type is not available')

                #execute (call)
                self.action_hooks[act_type](act)

    def apply_button_scheme(self, scheme_name, root_widget):
        if scheme_name not in self.button_schemes:
            Logger.warning('USERCFGMAN: invalid scheme "{}" requested'.format(scheme_name))

        #reset to default
        for group_name in KEY_GROUP_LIST:
            root_widget.ids[group_name].set_all_child_property('disabled', False)
            root_widget.ids[group_name].set_all_child_property('remote_node', '')
            root_widget.ids[group_name].set_all_child_property('remote_name', '')
            root_widget.ids[group_name].set_all_child_property('key_name', '')

        for group_name, actions in self.button_schemes[scheme_name].get_group_scheme().iteritems():
            if group_name not in root_widget.ids:
                Logger.warning('USERCFGMAN: invalid key group "{}" in scheme "{}"'.format(group_name, scheme_name))
                continue

            for item_name, item_cfg in actions.iteritems():

                #if item_name == 'global':
                #    continue
                if item_name == 'global':
                    #don't know why ids dont work properly
                    for attr_name, attr_val in actions['global'].iteritems():
                        root_widget.ids[group_name].set_all_child_property(attr_name, attr_val)
                    continue

                if item_name not in root_widget.ids:
                    Logger.warning('USERCFGMAN: no key "{}" in group "{}", requested in scheme "{}"'.format(item_name, group_name, scheme_name))
                    continue

                #try to apply
                for attr_name, attr_val in item_cfg.iteritems():
                    apply_to = root_widget.ids[item_name]
                    apply_to.__setattr__(attr_name, attr_val)

        Logger.info('USERCFGMAN: applying scheme "{}"'.format(scheme_name))
