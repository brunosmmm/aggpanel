#import pyjsonrpc
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.logger import Logger
from jnius import JavaException, autoclass

class Agg(FloatLayout):
    pass

class AggApp(App):

    def build(self):
        return Agg()

if __name__ == "__main__":

    is_android = False
    #detect android
    try:
        Context = autoclass('android.content.Context')
        from discover.android import AndroidListener
        Logger.info('android detected, using nsd service')
        listener = AndroidListener('_http._tcp', Context)
        is_android = True
    except JavaException:
        #class not found!
        Logger.info('android not detected, loading zeroconf')
        from discover.linux import LinuxListener
        listener = LinuxListener('_http._tcp.local.')

    listener.start_listening()
    AggApp().run()
    listener.stop_listening()
