from pyNCSre.api.ComAPI import *
import pyCAER.client as caerclient
from pyCAER.utils import doc_inherit, getuser, flatten
import time, ftplib
import os
from pyNCSre.pyST import events
from pyNCSre.pyST import channelEvents

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
        
        try:
            if (stim_kwargs['spikefile'] is not None):
                self.send_transfer(stim_kwargs['spikefile'])
        except:
            pass
        
        self.out = self.client.stimulate(stimulus, **stim_kwargs)
        return self.out

    def open(self):
        self._isopen = True
        self.client = caerclient.AEDATClient(*self.args, **self.kwargs)
        self.client.start()

    def close(self):
        self._isopen = False
        self.client.stop()
        
    def send_transfer(self, stimulus, s_file ):
        """ updates the remote file with the local one """
        one_isi = 11.11 # ns
        isi_base = 900
#         isi_scale = isi_base * one_isi / 1000 # microseconds
        isi_scale = 1
        dest_dir = '/var/opt/pyncs/'
        s_path = os.getcwd() + '/' + s_file
        dest_file = '{}_{}'.format(s_file,getuser())
        ftp = ftplib.FTP(self.kwargs['host'], user='pyncs')
#         ftp.set_debuglevel(2)
        
        conf = self.neurosetup.chips['U0'].configurator
        
        with open( s_path, 'w' ) as f:
            for stim in stimulus:
                isi = int(round(stim[1] * isi_scale))
                if ( isi > 2**16-1 ):
                    isi = 2**16-1
                f.write( '{},{}\n'.format(stim[0] & (2**14-1), isi ))

        with open( s_path, 'rb' ) as f:
            ftp.storlines('STOR {}'.format( dest_file ), f)
            ftp.close()

        conf.set_caer_sshs("/fpgaSpikeGen/", "Run", 'bool', "false")
        time.sleep(.2)    
        conf.set_caer_sshs("/fpgaSpikeGen/", "VariableISI", 'bool', "true")
        conf.set_caer_sshs("/fpgaSpikeGen/", "ISIBase", 'int', '{}'.format(isi_base))
        conf.set_caer_sshs("/fpgaSpikeGen/", "StimFile", 'string', dest_dir + dest_file)
        conf.set_caer_sshs("/fpgaSpikeGen/", "WriteSRAM", 'bool', "true")
        time.sleep(1)
        conf.set_caer_sshs("/fpgaSpikeGen/", "Repeat", 'bool', "true")
        conf.set_caer_sshs("/fpgaSpikeGen/", "Run", 'bool', "true")
