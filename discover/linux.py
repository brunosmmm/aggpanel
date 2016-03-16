from zeroconf import ServiceBrowser, Zeroconf
from kivy.logger import Logger

class LinuxListener(object):
    def __init__(self, service_type):

        self.service_type = service_type
        self.zeroconf = None
        self.browser = None

    def start_listening(self):
        self.zeroconf = Zeroconf()
        self.browser = ServiceBrowser(self.zeroconf, self.service_type, self)

    def stop_listening(self):
        self.zeroconf.close()

    def remove_service(self, zeroconf, type, name):
        Logger.info("Service %s removed" % (name,))

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        Logger.info("Service %s added, service info: %s" % (name, info))
