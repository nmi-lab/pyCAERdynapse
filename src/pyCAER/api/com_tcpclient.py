from pyNCSre.api.ComAPI import *
import pyCAER.client as caerclient
from pyCAER.utils import doc_inherit

#Has a single client.
#Instanciated object can be reused


class Communicator(ContinuousCommunicatorBase):
    '''
    This class implements the BatchCommunicator API defined by the NCS tools.
    It uses the "AEX net client" to connect of the AEX server of the target host, using TCP.

    Inputs:
    *host:* the hostname of the computer where the AEX board is attached (default: localhost). If localhost is chosen, then ssh commands are *not* used.
    for additional arguments, refer to caerclient.netClient.

    See also:
    `netClient <#pyCaer.caerclient.netClient>`_

    Usage:
    >>> c = Communicator(host = 'localhost', devnum = 0)
    >>> c.run()
    '''
    def __init__(self, *netclient_args, **netclient_kwargs):
        self.args = netclient_args
        self.kwargs = netclient_kwargs
        self.kwargs['autostart'] = False
        self.out = caerclient.pyST.events()
        self._client = None
        ContinuousCommunicatorBase.__init__(self)

    @property
    def client(self):
        if self._client != None:
            return self._client
        else:
            return None

    @client.setter
    def client(self, value):
        if self._client != None and self.client.is_alive():
            self.close()
        self._client = value

    def run(self, stimulus=None, duration=1000, context_manager=None, **kwargs):    
        self.open()
        self.stim(stimulus, duration, context_manager, **kwargs)
        self.close()
        return self.out

    def mon(self, duration):
        return self.client.fetch()

    def stim(self, stimulus, duration=None, context_manager=None, **stim_kwargs):
        stim_kwargs.update([
            ['tDuration', duration],
            ['context', context_manager]])
        self.out = self.client.stimulate(stimulus, **stim_kwargs)
        return self.out

    def open(self):
        self._isopen = True
        self.client = caerclient.AEDATClient(*self.args, **self.kwargs)
        self.client.start()

    def close(self):
        self._isopen = False
        self.client.stop()
