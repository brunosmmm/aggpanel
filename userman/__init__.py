import json
import os
from userman.exception import *
from kivy.logger import Logger
import re

USER_ACTION_LIST = ['send_remote_key']
JSON_FILE_REGEX = re.compile(r'.*\.json$')

class UserAction(object):
    def __init__(self, description, action_list):
        self.desc = description
        self.action_list = action_list

    def get_action_list(self):
        return self.action_list

class UserConfigManager(object):
    def __init__(self, config_path, action_hook_dict):
        self.config_path = config_path
        self.user_actions = {}
        self.action_hooks = dict(action_hook_dict)

        self._scan_files()

    def _scan_files(self):
        folders = os.walk(self.config_path).next()[1]

        for folder in folders:
            if folder == 'actions':
                files = os.walk(os.path.join(self.config_path, folder)).next()[2]
                for fname in files:
                    if JSON_FILE_REGEX.match(fname) != None:
                        Logger.info('USERCFGMAN: discovered action {}'.format(fname))
                        if self._load_action(os.path.join(self.config_path, folder, fname)) == False:
                            Logger.info('USERCFGMAN: failed to load {}'.format(fname))



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
