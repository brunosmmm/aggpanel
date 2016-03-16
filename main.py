#import pyjsonrpc
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.logger import Logger
from jnius import JavaException, autoclass
from agg.manager import AggManager
import re

class Agg(FloatLayout):
    pass

class AggApp(App):

    def build(self):
        return Agg()

def discover_service(address, port, name, attr):
    if AggManager.is_service_agg(name):
        #register!
        element = AggManager.get_element_from_name(name)
        aggman = AggManager(address=address,
                            port=port,
                            attr=attr,
                            element=element)

        Logger.info('agg-man: found aggregator server "{}" at {}:{}'.format(element,
                                                                            address,
                                                                            port))

def remove_service(name):
    if AggManager.is_service_agg(name):
        element = AggManager.get_element_from_name(name)

        Logger.info('agg-man: aggregator server "{}" was removed'.format(element))

if __name__ == "__main__":

    is_android = False
    #detect android
    try:
        Context = autoclass('android.content.Context')
        from discover.android import AndroidListener
        Logger.info('android detected, using nsd service')
        #no named arguments allowed here, wtf
        listener = AndroidListener('_http._tcp',
                                   Context,
                                   discover_service,
                                   remove_service)
        is_android = True
    except JavaException:
        #class not found!
        Logger.info('android not detected, loading zeroconf')
        from discover.linux import LinuxListener
        listener = LinuxListener('_http._tcp.local.',
                                 service_found_cb=discover_service,
                                 service_removed_cb=remove_service)

    listener.start_listening()
    AggApp().run()
    listener.stop_listening()
