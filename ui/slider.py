from kivy.uix.slider import Slider
from ui.misc import RootFinderMixin
from kivy.properties import ObjectProperty, NumericProperty

class RXVolumeSlider(Slider, RootFinderMixin):

    control_name = ObjectProperty('')

    manipulating_value = False

    def __init__(self, *args, **kwargs):
        super(RXVolumeSlider, self).__init__(*args, **kwargs)

        self.max = 16.5
        self.min = -80.0
        self.step = 0.5

    def on_value(self, *args, **kwargs):
        if self.manipulating_value == False:
            #flag root widget
            self.find_root().rx_slider_changed(self.control_name, self.value)

    def set_value(self, value):
        self.manipulating_value = True
        self.value = value
        self.manipulating_value = False
