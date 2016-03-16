import re
import pyjsonrpc

#compensate unknown android weirdness
AGGREGATOR_REGEX = re.compile(r'^PeriodicPi(\s|\\032)Aggregator(\s|\\032)\[([a-zA-Z0-9]+)\]')

class AggManager(object):
    def __init__(self, address, port, attr, element):
        self.agg_addr = address
        self.agg_port = port
        self.agg_attr = attr
        self.agg_element = element

    @staticmethod
    def get_element_from_name(name):
        return AGGREGATOR_REGEX.match(name).group(3)

    @staticmethod
    def is_service_agg(name):

        m = AGGREGATOR_REGEX.match(name)
        if m != None:
            return True

        return False
