import kivy
kivy.require('1.9.0')
from kivy.config import Config
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')
Config.set('graphics', 'resizable', '0')
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.logger import Logger
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle
import kivy.uix.effectwidget as ew
from kivy.uix.widget import Widget
from kivy.core.image import Image
from jnius import JavaException, autoclass
from agg.manager import AggManager
import re
from userman import UserConfigManager
from collections import deque
from kivy.clock import Clock
from kivy.core.window import Window

IMAGE_PATH = 'img'
KEY_CLASS_IMAGES = { 'KeyDown'        : {'img': 'down',
                                         'color_up' : 'AA7E39',
                                         'color_down' : 'D4AB6A'},
                     'KeyUp'          : {'img': 'up',
                                         'color_up' : 'AA7E39',
                                         'color_down' : 'D4AB6A'},
                     'KeyLeft'        : {'img': 'left',
                                         'color_up' : 'AA7E39',
                                         'color_down' : 'D4AB6A'},
                     'KeyRight'       : {'img': 'right',
                                         'color_up' : 'AA7E39',
                                         'color_down' : 'D4AB6A'},
                     'KeyPower'       : {'img': 'power',
                                         'color_up' : '2B4A6F',
                                         'color_down' : '4B688B'},
                     'KeyFastForward' : {'img': 'ff',
                                         'color_up' : '2B823A',
                                         'color_down' : '51A35F'},
                     'KeyRewind'      : {'img': 'rew',
                                         'color_up' : '2B823A',
                                         'color_down' : '51A35F'},
                     'KeyBack'        : {'img': 'back',
                                         'color_up' : '2B4A6F',
                                         'color_down' : '4B688B'},
                     'KeyPlay'        : {'img': 'play',
                                         'color_up' : '2B823A',
                                         'color_down' : '51A35F'},
                     'KeyHome'        : {'img': 'home',
                                         'color_up' : '2B4A6F',
                                         'color_down' : '4B688B'},
                     'KeyVolUp'        : {'img': 'speaker-3',
                                         'color_up' : 'AA4139',
                                          'color_down' : 'D4726A'},
                     'KeyVolDn'        : {'img': 'speaker-2',
                                         'color_up' : 'AA4139',
                                          'color_down' : 'D4726A'},
                     'KeyMute'        : {'img': 'speaker-4',
                                         'color_up' : 'AA4139',
                                         'color_down' : 'D4726A'},
                     'KeyMenu'        : {'img': 'menu',
                                         'color_up' : '2B4A6F',
                                         'color_down' : '4B688B'},
                     'KeyOK'       : {'img': 'check',
                                         'color_up' : 'AA7E39',
                                         'color_down' : 'D4AB6A'},
                     'KeyRefreshBack'       : {'img': 'refresh',
                                         'color_up' : '2B4A6F',
                                         'color_down' : '4B688B'}
                     }

def hex_color_to_rbg(h):
    ret = tuple(float(int(h[i:i+2], 16))/255.0 for i in (0, 2 ,4))
    return ret

#wtf, kivy!!!
class RemoteKey(Button):

    bgup = ObjectProperty([0.,0.,0.])
    bgdown = ObjectProperty([0.,0.,0.])
    remote_name = ObjectProperty('')
    key_name = ObjectProperty('')
    execute_action = ObjectProperty('')

    def find_root(self):
        root = self.parent
        while isinstance(root, RootWidget) == False:
            root = root.parent

        return root

    def hextorgb(self, h):
        return tuple(float(int(h[i:i+2], 16))/255.0 for i in (0, 2 ,4))

    def set_bgcolor(self, color):
        img = self.ids['btnimg']
        tex = self.ids['btnimg'].texture
        img_size = [self.size[0], self.size[0]]
        img_pos = [self.pos[0], self.pos[1]+ (self.size[1]/2 - img_size[1]/2)]
        with self.canvas:
            Color(rgb=color)
            Rectangle(size=self.size, pos=self.pos)
            Color(rgb=(1.,1.,1.))
            Rectangle(texture=tex, size=img_size, pos=img_pos)

    def canvas_ready(self):
        return self.x_pos_set and self.y_pos_set and self.w_set and self.h_set

    def __init__(self, **kwargs):

        self.x_pos_set = False
        self.y_pos_set = False
        self.w_set = False
        self.h_set = False
        self.canvas_set = False

        super(RemoteKey, self).__init__(**kwargs)

    # def __setattr__(self, name, value):

    #     #if name == 'bgup' and self.canvas_ready():
    #     #    self.set_bgcolor(hex_color_to_rbg(value))
    #     #if name == 'bgdown' and self.canvas_ready():
    #     #    self.set_bgcolor(hex_color_to_rbg(value))

    #     if name == 'x':
    #         self.x_pos_set = True

    #     if name == 'y':
    #         self.y_pos_set = True

    #     if name == 'height':
    #         self.h_set = True

    #     if name == 'width':
    #         self.w_set = True

    #     super(RemoteKey, self).__setattr__(name, value)

    def on_press(self, **kwargs):
        self.set_bgcolor(hex_color_to_rbg(self.bgdown))
        #execute action has priority over direct remote key access
        if self.execute_action != '':
            self.find_root().execute_action(self.execute_action)
        else:
            self.find_root().key_press(self.remote_name, self.key_name)

    def on_release(self, **kwargs):
        self.set_bgcolor(hex_color_to_rbg(self.bgup))


#button class template
def make_button_class(class_name, img_up, img_down, img_path, color_down='000000', color_up='000000'):
    template = """
<{cls}@RemoteKey>:
    canvas:
        Color:
            rgb: self.hextorgb('{bgup}')
        Rectangle:
            size: self.size
            pos: self.pos
    bgup: '{bgup}'
    bgdown: '{bgdn}'
    background_normal: 'img/white.png'
    #background_down: ''#''
    border: 0,0,0,0
    Image:
        id: btnimg
        source: '{btnimg}'
        y: self.parent.y
        x: self.parent.x
        size: self.parent.size
        mipmap: True
""".format(cls=class_name, bgup=color_up, bgdn=color_down,
           btnimg='{}/{}.png'.format(img_path, img_up))
           #'{}/{}.png'.format(img_path, img_down))
    Builder.load_string(template)

for key_class, key_prop in KEY_CLASS_IMAGES.iteritems():
    make_button_class(key_class, key_prop['img'], key_prop['img'], IMAGE_PATH,
                      key_prop['color_down'], key_prop['color_up'])

class RootWidget(FloatLayout):
    def __init__(self, *args, **kwargs):
        super(RootWidget, self).__init__(*args, **kwargs)
        self.active_aggregator = None
        self.userman = UserConfigManager('user', {})
        self.act_queue = deque()

        #register action types
        self.userman.register_action_hook('send_remote_key', self._action_key_press)
        Clock.schedule_interval(self._check_action_queue, 0.1)

    def _queue_action(self, action_cb, **kwargs):
        self.act_queue.append([action_cb, kwargs])

    def _action_key_press(self, key_data):
        if 'remote_name' not in key_data or 'key_name' not in key_data:
            return

        self._queue_action(self._key_press, **key_data)

    def _check_action_queue(self, dt):
        if len(self.act_queue) > 0:
            action = self.act_queue.popleft()
            Logger.info('QUEUE: popped {}'.format(action))
            if action[0]:
                #call
                action[0](**action[1])

    def set_active_aggregator(self, aggregator):
        #if aggregator != None:
        #    self.ids.main_grid.disabled = False
        #else:
        #    self.ids.main_grid.disabled = True
        self.active_aggregator = aggregator

    def execute_action(self, action_name):
        self.userman.execute_action(action_name)

    def key_press(self, remote_name, key_name):
        self._queue_action(self._key_press,
                           remote_name=remote_name,
                           key_name=key_name)

    def _key_press(self, remote_name, key_name):
        Logger.info('KEYPRESS: sending "{}" to remote "{}"'.format(key_name, remote_name))
        if self.active_aggregator != None:
            if remote_name != '' and key_name != '':
                self.active_aggregator.key_press(remote_name, key_name)

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
