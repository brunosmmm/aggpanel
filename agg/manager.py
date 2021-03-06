import re
import pyjsonrpc
from kivy.logger import Logger
from threading import Thread
from collections import deque
import time

#compensate unknown android weirdness
AGGREGATOR_REGEX = re.compile(r'^PeriodicPi(\s|\\032)Aggregator(\s|\\032)\[([a-zA-Z0-9]+)\]')
IPV6_REGEX = re.compile(r'[0-9a-fA-F]{0,4}::(([0-9a-fA-F]{0,4}):){3}[0-9a-fA-F]{0,4}')

class AggManager(object):
    def __init__(self, address, port, attr, element):
        self.agg_addr = address
        self.agg_port = port
        self.agg_attr = attr
        self.agg_element = element
        self.server_drv_list = []
        self.request_queue = deque()

        #make client
        Logger.info('agg-{}: connecting at {}:{}'.format(self.agg_element, self.agg_addr, self.agg_port))
        if IPV6_REGEX.match(self.agg_addr) != None:
            self.agg_addr = '[{}]'.format(self.agg_addr)
        self.client = pyjsonrpc.HttpClient(url='http://{}:{}/'.format(self.agg_addr, self.agg_port))

        #get information
        self.refresh_driver_list()

        #spawn thread
        self.stop = False
        Thread(target=self._next_request).start()


    def __getattribute__(self, name):
        #try to parse
        try:
            inst_name, prop_name = name.split('__')

            if inst_name not in self.server_drv_list:
                if inst_name.replace('_', '-') in self.server_drv_list:
                    inst_name = inst_name.replace('_', '-')
                else:
                    raise AttributeError

            return self.get_module_property(inst_name, prop_name)
        except:
            pass

        return super(AggManager, self).__getattribute__(name)

    def __setattr__(self, name, value):

        try:
            inst_name, prop_name = name.split('__')

            if inst_name not in self.server_drv_list:
                if inst_name.replace('_', '-') in self.server_drv_list:
                    inst_name = inst_name.replace('_', '-')
                else:
                    raise AttributeError

            return self.set_module_property(inst_name, prop_name, value)
        except:
            pass

        return super(AggManager, self).__setattr__(name, value)

    def _next_request(self):

        while self.stop == False:
            if len(self.request_queue) > 0:
                request = self.request_queue.popleft()
                if request['req'] == 'get_property':
                    value = self.client.module_get_property(request['inst_name'], request['prop_name'])
                    if request['callback'] != None:
                        request['callback'](value)
                elif request['req'] == 'set_property':
                    self.client.module_set_property(request['inst_name'], request['prop_name'], request['value'])
                    if request['callback'] != None:
                        request['callback'](request['prop_name'])
                elif request['req'] == 'call_method':
                    retval = self.client.module_call_method(request['inst_name'], request['method_name'], **request['kwargs'])
                    if request['callback'] != None:
                        request['callback'](retval)


            time.sleep(0.1)

    def get_module_property(self, inst_name, prop_name, block=True, callback=None):
        if inst_name not in self.server_drv_list:
            return

        ret_val = None
        try:
            if block:
                while len(self.request_queue) > 0:
                    pass

                return self.client.module_get_property(inst_name,
                                                       prop_name)
            #else
            self.request_queue.append({'req': 'get_property',
                                       'inst_name': inst_name,
                                       'prop_name': prop_name,
                                       'callback': callback})

        except:
            Logger.warning('could not read property "{}" of instance "{}"'.format(inst_name,
                                                                                  prop_name))
        return None

    def set_module_property(self, inst_name, prop_name, value, block=True, callback=None):
        if inst_name not in self.server_drv_list:
            return

        try:
            if block:
                while len(self.request_queue) > 0:
                    pass

                return self.client.module_set_property(inst_name,
                                                       prop_name,
                                                       value)

            #else
            self.request_queue.append({'req' : 'set_property',
                                       'inst_name': inst_name,
                                       'prop_name': prop_name,
                                       'value': value,
                                       'callback': callback})

        except:
            Logger.warning('could not write property "{}" of instance "{}"'.format(inst_name,
                                                                                  prop_name))
        return None

    def call_module_method(self, inst_name, method_name, block=True, callback=None, **kwargs):
        if inst_name not in self.server_drv_list:
            return None

        try:
            if block:
                while len(self.request_queue) > 0:
                    pass

                return self.client.module_call_method(inst_name,
                                                      method_name,
                                                      **kwargs)
            #else
            self.request_queue.append({'req': 'call_method',
                                       'inst_name': inst_name,
                                       'method_name': method_name,
                                       'callback': callback,
                                       'kwargs': kwargs})
        except:
            Logger.warning('failed to call method "{}" of instance "{}"'.format(inst_name,
                                                                                method_name))

        return None


    def refresh_driver_list(self):
        self.server_drv_list = self.client.call('list_drivers')

    def key_press(self, remote_node, remote_name, key_name, repeat_count=0):
        self.call_module_method('lircd-{}'.format(remote_node),
                                'send_remote_key',
                                remote_name=remote_name,
                                key_name=key_name,
                                repeat_count=repeat_count)

    def start_key_press(self, remote_node, remote_name, key_name):
        self.call_module_method('lircd-{}'.format(remote_node),
                                'start_key_press',
                                remote_name=remote_name,
                                key_name=key_name)

    def is_driver_present(self, driver_name):
        return driver_name in self.server_drv_list

    @staticmethod
    def get_element_from_name(name):
        return AGGREGATOR_REGEX.match(name).group(3)

    @staticmethod
    def is_service_agg(name):

        m = AGGREGATOR_REGEX.match(name)
        if m != None:
            return True

        return False
