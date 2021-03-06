from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import ObjectProperty
from kivy.logger import Logger
from ui.misc import RootFinderMixin

class PanelActionBehavior(RootFinderMixin):
    execute_action = ObjectProperty('')
    load_scheme = ObjectProperty('')

    def __init__(self, *args, **kwargs):
        if 'root_widget_class' not in kwargs:
            self.root_widget_class = 'RootWidget'
        else:
            self.root_widget_class = kwargs['root_widget_class']

    def trigger_event(self):

        if self.load_scheme != '':
            self.find_root().activate_button_configuration(self.load_scheme)

        #execute action has priority over direct remote key access
        if self.execute_action != '':
            self.find_root().execute_action(self.execute_action)

class PanelToggleActionButton(ToggleButton, PanelActionBehavior):
    def on_press(self, *args, **kwargs):
        self.trigger_event()
        super(PanelToggleActionButton, self).on_press(*args, **kwargs)

class RemoteKey(Button, PanelActionBehavior):

    bgup = ObjectProperty(None)
    bgdown = ObjectProperty(None)
    bgdis = ObjectProperty(None)
    remote_node = ObjectProperty('')
    remote_name = ObjectProperty('')
    key_name = ObjectProperty('')
    is_toggle = ObjectProperty(False)

    def hextorgb(self, h):
        if h == None:
            return None
        return tuple(float(int(h[i:i+2], 16))/255.0 for i in (0, 2 ,4))

    def set_bgcolor(self, color):
        if color == None:
            return

        has_img = False
        if self.ids['btnimg'].source != '':
            tex = self.ids['btnimg'].texture
            has_img = True

        if self.size[0] > self.size[1]:
            img_size = [self.size[1], self.size[1]]
        else:
            img_size = [self.size[0], self.size[0]]

        img_pos = [self.pos[0] + (self.size[0]/2 - img_size[0]/2), self.pos[1]+ (self.size[1]/2 - img_size[1]/2)]
        self.canvas.clear()
        with self.canvas:
            Color(rgb=color)
            RoundedRectangle(size=self.size, pos=self.pos)
            if has_img:
                Color(rgb=(1.,1.,1.))
                Rectangle(texture=tex, size=img_size, pos=img_pos)

    def canvas_ready(self):
        return self.x_pos_set and self.y_pos_set and self.w_set and self.h_set

    def __init__(self, *args, **kwargs):

        self.x_pos_set = False
        self.y_pos_set = False
        self.w_set = False
        self.h_set = False
        self.canvas_set = False
        self.toggle_state = False

        self.inhibit = True

        kwargs.update({'root_widget_class' : 'RootWidget'})
        super(RemoteKey, self).__init__(*args, **kwargs)

        self.bind(size=self.redraw)

    def __setattr__(self, attr, value):
        super(RemoteKey, self).__setattr__(attr, value)

        #hacky hack to simplify remote zoning
        if attr == 'parent':
            try:
                self.remote_node = self.parent.remote_node
            except Exception as ex:
                Logger.info('DEBUG: {}'.format(ex))

    def on_press(self, **kwargs):
        if self.is_toggle:
            if self.toggle_state:
                self.set_bgcolor(self.hextorgb(self.bgdown))
            else:
                self.set_bgcolor(self.hextorgb(self.bgup))

            self.toggle_state = not self.toggle_state
        else:
            self.set_bgcolor(self.hextorgb(self.bgdown))

        if self.load_scheme != '':
            self.find_root().activate_button_configuration(self.load_scheme)

        #execute action has priority over direct remote key access
        if self.execute_action != '':
            self.find_root().execute_action(self.execute_action)
        else:
            self.find_root().key_press(self.remote_node, self.remote_name, self.key_name)

    def on_release(self, **kwargs):
        if not self.is_toggle:
            self.set_bgcolor(self.hextorgb(self.bgup))

    def on_disabled(self, *args, **kwargs):
        super(RemoteKey, self).on_disabled(*args, **kwargs)

        if self.inhibit == True:
            return

        if args[1] == True:
            self.set_bgcolor(self.hextorgb(self.bgdis))
        else:
            self.set_bgcolor(self.hextorgb(self.bgup))

    def redraw(self, *args):
        if self.disabled:
            self.set_bgcolor(self.hextorgb(self.bgdis))
        else:
            if self.state == 'down':
                self.set_bgcolor(self.hextorgb(self.bgdown))
            else:
                self.set_bgcolor(self.hextorgb(self.bgup))
