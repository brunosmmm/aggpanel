from kivy.uix.spinner import Spinner
from ui.misc import RootFinderMixin
from kivy.logger import Logger
from kivy.properties import ObjectProperty

_RX_SOURCES = ['AV1', 'AV2', 'AV3', 'AV4', 'AV5', 'AV6', 'AV7', 'AUDIO1', 'AUDIO2', 'AUDIO3', 'AUDIO4', 'TUNER', 'USB', 'V-AUX', 'SERVER', 'OFF', 'AirPlay', 'MULTI CH', 'NET RADIO', 'PHONO', 'Pandora', 'Rhapsody', 'SiriusXM', 'iPod (USB)']

class SourceSpinner(Spinner, RootFinderMixin):

    zone = ObjectProperty('')

    def __init__(self, *args, **kwargs):
        super(SourceSpinner, self).__init__(*args, **kwargs)

        self.values = []
        self.values = _RX_SOURCES[:]

        self.updating = False

    def update_source(self, source):
        if source not in self.values:
            return

        self.updating = True
        self.text = source

        if self.text == 'OFF':
            self.disabled = True
        else:
            self.disabled = False

        self.updating = False

    def on_text(self, *args, **kwargs):
        if self.updating:
            return

        #set source
        self.find_root().select_input(self.zone, self.text)

    def on_is_open(self, spinner, is_open):
        super(SourceSpinner, self).on_is_open(spinner, is_open)

        if is_open:
            self.find_root().stop_refreshing = True
        else:
            self.find_root().stop_refreshing = False

    def on_press(self, *args):
        if self.is_open == False:
            #opening
            pass
