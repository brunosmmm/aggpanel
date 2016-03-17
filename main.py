#import pyjsonrpc
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.logger import Logger
from kivy.properties import ObjectProperty
from jnius import JavaException, autoclass
from agg.manager import AggManager
import re

class Agg(FloatLayout):

    def __init__(self, *args, **kwargs):
        super(Agg, self).__init__(*args, **kwargs)
        self.active_aggregator = None

    def set_active_aggregator(self, aggregator):
        if aggregator != None:
            self.ids.main_grid.disabled = False
        else:
            self.ids.main_grid.disabled = True
        self.active_aggregator = aggregator

    def key_press(self, remote_name, key_name):
        if self.active_aggregator != None:
            self.active_aggregator.key_press(remote_name, key_name)

class AggApp(App):
    def __init__(self, *args, **kwargs):
        super(AggApp, self).__init__(*args, **kwargs)
        self.app = None
        self.listener = None
        self.aggregators = {}

    def build(self):
        self.app = Agg()
        #self.listener.start_listening()
        return self.app

    def run(self, *args, **kwargs):
        super(AggApp, self).run(*args, **kwargs)
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

if __name__ == "__main__":

    main_app = AggApp()

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
