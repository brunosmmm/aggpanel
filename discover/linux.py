from zeroconf import ServiceBrowser, Zeroconf
from kivy.logger import Logger
import re

ZEROCONF_PATTERN = re.compile(r'^([^\.]+).*')

class LinuxListener(object):
    def __init__(self, service_type, service_found_cb=None, service_removed_cb=None):

        self.service_type = service_type
        self.zeroconf = None
        self.browser = None

        self.cb_found = service_found_cb
        self.cb_removed = service_removed_cb

    def start_listening(self):
        self.zeroconf = Zeroconf()
        self.browser = ServiceBrowser(self.zeroconf, self.service_type, self)

    def stop_listening(self):
        self.zeroconf.close()

    def remove_service(self, zeroconf, type, name):
        Logger.info('linux-listener: service "{}" removed'.format(name))

        if self.cb_removed:
            self.cb_removed(name)

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        #get rid of annoying format
        m = ZEROCONF_PATTERN.match(name)
        #annoying address representation also!
        addr = '.'.join([str(ord(x)) for x in info.address])

        Logger.info('linux-listener: service "{}" added, service info: {}'.format(m.group(1), info))

        if self.cb_found:
            self.cb_found(address=addr,
                          port=info.port,
                          name=m.group(1),
                          attr=[])
