import kivy
kivy.require('1.9.1')
from kivy.config import Config
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')
Config.set('graphics', 'resizable', '0')
from kivy.properties import ObjectProperty
from kivy.logger import Logger
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle
import kivy.uix.effectwidget as ew
from jnius import JavaException, autoclass
from agg.manager import AggManager
from userman import UserConfigManager
from collections import deque
from kivy.clock import Clock
from kivy.core.window import Window
from ui.remotekey import RemoteKey, PanelToggleActionButton
from ui.keygrid import KeyGrid
import json

IMAGE_PATH = 'img'
with open('ui/config/keys.json', 'r') as f:
    KEY_CLASS_IMAGES = json.load(f)

def hex_color_to_rbg(h):
    ret = tuple(float(int(h[i:i+2], 16))/255.0 for i in (0, 2 ,4))
    return ret

#button class template
def make_button_class(class_name, img_up, img_down, img_path, color_down='000000', color_up='000000', color_dis='000000'):
    template = """
<{cls}@RemoteKey>:
    canvas:
        Clear
        Color:
            rgb: self.hextorgb('{bgdis}' if self.disabled else '{bgup}')
        RoundedRectangle:
            size: self.size
            pos: self.pos
    bgup: '{bgup}'
    bgdown: '{bgdn}'
    bgdis: '{bgdis}'
    #background_normal: 'img/white.png'
    #background_down: ''#''
    border: 0,0,0,0
    Image:
        id: btnimg
        source: '{btnimg}'
        y: self.parent.y
        x: self.parent.x
        size: self.parent.size
        mipmap: True
""".format(cls=class_name, bgup=color_up, bgdn=color_down, bgdis=color_dis,
           btnimg=('{}/{}.png'.format(img_path, img_up) if img_up != '' else ''))
    Builder.load_string(template)

for key_class, key_prop in KEY_CLASS_IMAGES.iteritems():
    make_button_class(key_class, key_prop['img'], key_prop['img'], IMAGE_PATH,
                      key_prop['color_down'], key_prop['color_up'], key_prop['color_dis'])

class RootWidget(FloatLayout):

    _panel_list = ['bluray_panel', 'ctrl_panel', 'action_panel', 'receiver_panel']

    def __init__(self, *args, **kwargs):
        super(RootWidget, self).__init__(*args, **kwargs)
        self.active_aggregator = None
        self.act_queue = deque()
        self.userman = UserConfigManager('user', {}, self)

        #attach events
        self.userman.attach_event_hook('user_data_loaded', self._load_default_schemes)

        #register action types
        self.userman.register_action_hook('send_remote_key', self._action_key_press)
        self.userman.register_action_hook('start_key_press', self._action_start_key_press)
        self.userman.register_action_hook('wait', self._insert_wait)
        Clock.schedule_interval(self._check_action_queue, 0.1)

        #scan user files
        self.userman.scan_files()

    def _load_default_schemes(self):
        pass
        #Logger.info('DEBUG: user data has been loaded')

    def _queue_action(self, action_cb, **kwargs):
        self.act_queue.append([action_cb, kwargs])

    def _action_key_press(self, key_data):
        if 'remote_name' not in key_data or 'key_name' not in key_data:
            return

        self._queue_action(self._key_press, **key_data)

    def _action_start_key_press(self, key_data):
        if 'remote_name' not in key_data or 'key_name' not in key_data:
            return

        self._queue_action(self._rpt_key_press, **key_data)

    def _insert_wait(self, wait_data):
        if 'amount' not in wait_data:
            return

        for i in range(wait_data['amount']):
            self._queue_action(None)

    def _check_action_queue(self, dt):
        if len(self.act_queue) > 0:
            action = self.act_queue.popleft()
            Logger.info('QUEUE: popped {}'.format(action))
            if action[0]:
                #call
                action[0](**action[1])

    def set_active_aggregator(self, aggregator):
        for panel_id in self._panel_list:
            if aggregator != None:
                self.ids[panel_id].disabled = False
                self.activate_button_configuration(None)
            else:
                self.ids[panel_id].disabled = True

        self.active_aggregator = aggregator

    def execute_action(self, action_name):
        self.userman.execute_action(action_name)

    def key_press(self, remote_node, remote_name, key_name):
        self._queue_action(self._key_press,
                           remote_node=remote_node,
                           remote_name=remote_name,
                           key_name=key_name)

    def _key_press(self, remote_node, remote_name, key_name, repeat_count=0):
        if self.active_aggregator != None:
            if remote_name != '' and key_name != '' and remote_node != '':
                Logger.info('KEYPRESS: sending "{}" to remote "{}" at node "{}"'.format(key_name, remote_name, remote_node))
                self.active_aggregator.key_press(remote_node, remote_name, key_name, repeat_count)

    def _rpt_key_press(self, remote_node, remote_name, key_name, rpt_count=0):
        if self.active_aggregator != None:
            if remote_name != '' and key_name != '' and remote_node != '':
                Logger.info('KEYPRESS: sending "{}" to remote "{}" at node "{}"'.format(key_name, remote_name, remote_node))
                self.active_aggregator.start_key_press(remote_node, remote_name, key_name, rpt_count)

    def activate_button_configuration(self, scheme_name):
        if scheme_name == None:
            self.userman.reset_button_scheme()
        else:
            self.userman.apply_button_scheme(scheme_name)

class MainApp(App):

    def __init__(self, *args, **kwargs):
        super(MainApp, self).__init__(*args, **kwargs)
        self.app = None
        self.listener = None
        self.aggregators = {}

    def build(self):
        self.app = RootWidget()
        self.listener.start_listening()
        return self.app

    def run(self, *args, **kwargs):
        Window.size = (1280, 720)
        super(MainApp, self).run(*args, **kwargs)
        self.listener.stop_listening()

    def set_listener(self, listener):
        self.listener = listener

    def discover_service(self, address, port, name, attr):
        if AggManager.is_service_agg(name):
            #register!
            element = AggManager.get_element_from_name(name)
            aggman = AggManager(address=address,
                                port=port,
                                attr=attr,
                                element=element)

            #support several aggregators?
            self.aggregators['element'] = aggman

            Logger.info('agg-man: found aggregator server "{}" at {}:{}'.format(element,
                                                                                address,
                                                                                port))
            #set active default for now
            self.app.set_active_aggregator(aggman)

    def remove_service(self, name):
        if AggManager.is_service_agg(name):
            element = AggManager.get_element_from_name(name)

            if element in self.aggregators:
                del self.aggregators['element']

            Logger.info('agg-man: aggregator server "{}" was removed'.format(element))

            self.app.set_active_aggregator(None)

    def on_pause(self):
        #self.listener.stop_listening(block=True)
        return True

    def on_resume(self):
        #self.listener.start_listening()
        pass

if __name__ == '__main__':

    main_app = MainApp()

    is_android = False
    #detect android
    try:
        Context = autoclass('android.content.Context')
        from discover.android import AndroidListener
        Logger.info('android detected, using nsd service')
        #no named arguments allowed here, wtf
        listener = AndroidListener('_http._tcp',
                                   Context,
                                   main_app.discover_service,
                                   main_app.remove_service)
        is_android = True
    except JavaException:
        #class not found!
        Logger.info('android not detected, loading zeroconf')
        from discover.linux import LinuxListener
        listener = LinuxListener('_http._tcp.local.',
                                 service_found_cb=main_app.discover_service,
                                 service_removed_cb=main_app.remove_service)

    main_app.set_listener(listener)
    main_app.run()
