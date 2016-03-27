from kivy.uix.slider import Slider
from ui.misc import RootFinderMixin
from kivy.properties import ObjectProperty, NumericProperty
from kivy.clock import Clock

class RXVolumeSlider(Slider, RootFinderMixin):

    control_name = ObjectProperty('')

    manipulating_value = False
    dragging = False

    def __init__(self, *args, **kwargs):
        super(RXVolumeSlider, self).__init__(*args, **kwargs)

        self.max = 16.5
        self.min = -80.0
        self.step = 0.5
        self.announce = True
        self.ack_pending = False

    def _enable_announce(self, *args):
        self.announce = True

    def _disable_announce(self):
        self.announce = False
        #re-enable in the future
        Clock.schedule_once(self._enable_announce, 0.5)

    def on_touch_down(self, touch):
        super(RXVolumeSlider, self).on_touch_down(touch)
        self.dragging = True

    def on_touch_up(self, touch):
        super(RXVolumeSlider, self).on_touch_up(touch)
        self.dragging = False
        self.find_root().rx_slider_changed(self.control_name, self.value)
        self.ack_pending = True

    def ack_change(self):
        self.ack_pending = False

    def on_value(self, *args, **kwargs):
        if self.manipulating_value == False:

            if self.announce:
                #flag root widget
                self.find_root().rx_slider_changed(self.control_name, self.value)
                self.ack_pending = True
                self._disable_announce()

    def set_value(self, value):

        if self.dragging or self.ack_pending:
            return

        self.manipulating_value = True
        self.value = value
        self.manipulating_value = False
