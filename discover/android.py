from kivy.logger import Logger
from jnius import autoclass, PythonJavaClass, java_method

class AndroidListener(PythonJavaClass):
    __javainterfaces__ = ['android/net/nsd/NsdManager$DiscoveryListener', 'android/net/nsd/NsdManager$ResolveListener']
    def __init__(self, service_type, android_context, service_found_cb=None, service_removed_cb=None):

        super(AndroidListener, self).__init__()
        self.service_type = service_type

        self.NsdManager = autoclass('android.net.nsd.NsdManager')
        PythonActivity = autoclass('org.renpy.android.PythonActivity')
        activity = PythonActivity.mActivity
        self.nsd_mgr = activity.getSystemService(android_context.NSD_SERVICE)

        #callbacks
        self.cb_found = service_found_cb
        self.cb_removed = service_removed_cb

    def start_listening(self):
        self.nsd_mgr.discoverServices('_http._tcp', self.NsdManager.PROTOCOL_DNS_SD, self)

    def stop_listening(self):
        self.nsd_mgr.stopServiceDiscovery(self)

    @java_method('(Ljava/lang/String;I)V')
    def onStopDiscoveryFailed(self, service_type, error_code):
        Logger.error('android-listen: failed to stop discovery of service type "{}" with error code: {}'.format(service_type, error_code))

    @java_method('(Ljava/lang/String;I)V')
    def onStartDiscoveryFailed(self, service_type, error_code):
        Logger.error('android-listen: failed to start discovery of service type "{}" with error code: {}'.format(service_type, error_code))

    @java_method('(Landroid/net/nsd/NsdServiceInfo;)V')
    def onServiceLost(self, service):
        Logger.info('android-listen: service was removed: {}'.format(service.toString()))

        if self.cb_removed:
            self.cb_removed(service.getServiceName())

    @java_method('(Landroid/net/nsd/NsdServiceInfo;)V')
    def onServiceFound(self, service):
        Logger.debug('android-listen: discovered service, resolving...')
        self.nsd_mgr.resolveService(service, self)

    @java_method('(Ljava/lang/String;)V')
    def onDiscoveryStopped(self, service_type):
        Logger.debug('android-listen: discovery stopped for service type "{}"'.format(service_type))

    @java_method('(Ljava/lang/String;)V')
    def onDiscoveryStarted(self, service_type):
        Logger.debug('android-listen: discovery started for service type "{}"'.format(service_type))

    @java_method('(Landroid/net/nsd/NsdServiceInfo;I)V')
    def onResolveFailed(self, service_info, error_code):
        Logger.debug('android-listen: resolve failed for "{}" with error code {}'.format(service_info.toString(), error_code))

    @java_method('(Landroid/net/nsd/NsdServiceInfo;)V')
    def onServiceResolved(self, service_info):
        Logger.info('android-listen: service resolved: {}'.format(service_info.toString()))

        #annoying escaped characters!
        #dont pass attributes for now
        if self.cb_found:
            self.cb_found(address=service_info.getHost().toString(),
                          port=service_info.getPort(),
                          name=service_info.getServiceName(),
                          attr=[])
