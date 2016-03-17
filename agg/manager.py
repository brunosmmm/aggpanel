import re
import pyjsonrpc
from kivy.logger import Logger

#compensate unknown android weirdness
AGGREGATOR_REGEX = re.compile(r'^PeriodicPi(\s|\\032)Aggregator(\s|\\032)\[([a-zA-Z0-9]+)\]')

class AggManager(object):
    def __init__(self, address, port, attr, element):
        self.agg_addr = address
        self.agg_port = port
        self.agg_attr = attr
        self.agg_element = element

        #make client
        Logger.info('agg-{}: connecting at {}:{}'.format(self.agg_element, self.agg_addr, self.agg_port))
        self.client = pyjsonrpc.HttpClient(url='http://{}:{}/'.format(self.agg_addr, self.agg_port))

    def key_press(self, remote_name, key_name):
        drv_list = self.client.call('list_drivers')

        if 'lircd' not in drv_list:
            return

        self.client.call('module_call_method',
                         'lircd',
                         'send_remote_key',
                         remote_name=remote_name,
                         key_name=key_name)

    @staticmethod
    def get_element_from_name(name):
        return AGGREGATOR_REGEX.match(name).group(3)

    @staticmethod
    def is_service_agg(name):

        m = AGGREGATOR_REGEX.match(name)
        if m != None:
            return True

        return False
