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
    def __init__(self, description, options, group_scheme):
        self.desc = description
        self.options = options
        self.scheme = group_scheme

    def get_option_state(self, option_name):
        if option_name in self.options:
            return self.options[option_name]

        return None

    def get_group_scheme(self):
        return self.scheme

class UserConfigManager(object):
    def __init__(self, config_path, action_hook_dict, root_widget, autoscan=False):
        self.config_path = config_path
        self.user_actions = {}
        self.button_schemes = {}
        self.action_hooks = dict(action_hook_dict)
        self.event_hooks = {'user_data_loaded' : []}
        self.root_widget = root_widget

        if autoscan:
            self.scan_files()

    def _trigger_event(self, hook_name):
        for callback in self.event_hooks[hook_name]:
            callback()

    def attach_event_hook(self, hook_name, callback):
        if hook_name not in self.event_hooks:
            return False

        Logger.info('USERCFGMAN: attaching callback {} to event "{}"'.format(callback, hook_name))
        self.event_hooks[hook_name].append(callback)
        return True

    def _scan_subfolder(self, path, discover_action):
        files = os.walk(path).next()[2]
        for fname in files:
            if JSON_FILE_REGEX.match(fname) != None:
                Logger.info('USERCFGMAN: discovered file {}'.format(fname))
                if discover_action(os.path.join(path, fname)) == False:
                    Logger.info('USERCFGMAN: failed to load {}'.format(fname))

    def _do_startup(self):

        try:
            with open(self.config_path+'/startup.json', 'r') as f:
                startup = json.load(f)
                if 'start_actions' in startup:
                    for action in startup['start_actions']:
                        self.execute_action(action)
                if 'load_schemes' in startup:
                    for scheme in startup['load_schemes']:
                        self.apply_button_scheme(scheme)

        except IOError:
            Logger.warning('USERCFGMAN: startup file is not present')
        except ValueError:
            Logger.error('USERCFGMAN: error loading startup file: syntax error')


    def scan_files(self):
        folders = os.walk(self.config_path).next()[1]

        for folder in folders:
            if folder == 'actions':
                self._scan_subfolder(os.path.join(self.config_path, folder), self._load_action)
            if folder == 'schemes':
                self._scan_subfolder(os.path.join(self.config_path, folder), self._load_scheme)

        #check startup file
        self._do_startup()

        #trigger event
        self._trigger_event('user_data_loaded')

    def register_action_hook(self, action_type, action_cb):
        self.action_hooks[action_type] = action_cb

    def _load_action(self, action_file):

        loaded = False
        try:
            with open(action_file, 'r') as f:
                act = json.load(f)
                self.user_actions[act['name']] = UserAction(act['description'],
                                                            act['actions'])
                loaded = True
        except ValueError:
            Logger.error('USERCFGMAN: could not load action from "{}": syntax error'.format(action_file))
        except IOError:
            Logger.error('USERCFGMAN: could not load action from "{}": I/O error'.format(action_file))

        if loaded:
            Logger.info('USERCFGMAN: loaded action "{}"'.format(act['name']))

        return loaded

    def _load_scheme(self, scheme_file):
        loaded = False

        try:
            with open(scheme_file, 'r') as f:
                scheme = json.load(f, object_pairs_hook=OrderedDict)
                scheme_options = {}
                if 'options' in scheme:
                    scheme_options = scheme['options']
                self.button_schemes[scheme['name']] = ButtonScheme(scheme['description'],
                                                                   scheme_options,
                                                                   scheme['scheme'])
                loaded = True
        except ValueError:
            Logger.error('USERCFGMAN: could not load scheme from "{}": syntax error'.format(scheme_file))
        except IOError:
            Logger.error('USERCFGMAN: could not load scheme from "{}": I/O error'.format(scheme_file))

        if loaded:
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
    def reset_button_scheme(self):
        #reset to default
        for group_name in KEY_GROUP_LIST:
            self.root_widget.ids[group_name].set_all_child_property('disabled', True)
            self.root_widget.ids[group_name].set_all_child_property('remote_node', '')
            self.root_widget.ids[group_name].set_all_child_property('remote_name', '')
            self.root_widget.ids[group_name].set_all_child_property('key_name', '')
            self.root_widget.ids[group_name].inhibit_children(False)
        #enable selector
        self.root_widget.ids['ctrlscheme_group'].inhibit_children(False)

    def apply_button_scheme(self, scheme_name):
        if scheme_name not in self.button_schemes:
            Logger.warning('USERCFGMAN: invalid scheme "{}" requested'.format(scheme_name))

        if self.button_schemes[scheme_name].get_option_state('do_not_reset') != True:
            self.reset_button_scheme()

        for group_name, actions in self.button_schemes[scheme_name].get_group_scheme().iteritems():
            if group_name not in self.root_widget.ids:
                Logger.warning('USERCFGMAN: invalid key group "{}" in scheme "{}"'.format(group_name, scheme_name))
                continue

            for item_name, item_cfg in actions.iteritems():

                #if item_name == 'global':
                #    continue
                if item_name == 'global':
                    #don't know why ids dont work properly
                    for attr_name, attr_val in actions['global'].iteritems():
                        self.root_widget.ids[group_name].set_all_child_property(attr_name, attr_val)
                    continue

                if item_name not in self.root_widget.ids:
                    Logger.warning('USERCFGMAN: no key "{}" in group "{}", requested in scheme "{}"'.format(item_name, group_name, scheme_name))
                    continue

                #try to apply
                for attr_name, attr_val in item_cfg.iteritems():
                    apply_to = self.root_widget.ids[item_name]
                    apply_to.__setattr__(attr_name, attr_val)

        Logger.info('USERCFGMAN: applying scheme "{}"'.format(scheme_name))
