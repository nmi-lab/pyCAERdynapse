from pyNCSre.api.ConfAPI import MappingsBase
from contextlib import contextmanager
from pyCAER.utils import doc_inherit, getuser, flatten 
from pyCAER.maputils import * 
from pyCAER.api.conf_tcpclient import Configurator
import numpy as np
import socket


class Mappings(MappingsBase):

    @doc_inherit
    def __init__(self, host='128.200.83.67', concatenated=True, local_directory='/tmp/', remote_directory='/var/opt/pyncs/', debug=True, *args, **kwargs):
        self.host = host
        self.debug = debug
        self.cur_mappings = []
        self.remote_directory = remote_directory
        self.local_directory = local_directory 
        self.filename = 'mapping_table_' + getuser()
        self.local_filename = self.local_directory+self.filename
        if concatenated:
            self.remote_filename = self.remote_directory + 'mapping_table'
        else:
            self.remote_filename = self.remote_directory + self.filename
        
        #self.clear_mappings()
        super(self.__class__, self).__init__()

    def register_neurosetup(self, neurosetup):
        '''
        Provides a link to the Neurosetup. This is useful for complex parameter
        configuration protocols requiring the sequencing and monitoring of
        address-events
        '''
        self._neurosetup_registered = True
        self._neurosetup = neurosetup
        print("TODO: Checking chip configurator")
        print(type(neurosetup.chips['U0'].configurator))

    @doc_inherit
    def add_mappings(self, mappings):
        mappings = np.array(mappings, dtype='uint32')
        n_connections = len(mappings)
        nsetup = self.neurosetup
        mon_chad = nsetup.mon.addrPhysicalExtract(mappings[:,0])
        seq_chad = nsetup.seq.addrPhysicalExtract(mappings[:,1])

        #channels = [i for i,c in enumerate(mon_chad) if c is not None ] 
        #assert len(channels) == 1, 'cross chip connections not yet supported'
        
        src_chip = nsetup.mon.extract_channels(mappings[:,0])
        dst_chip = nsetup.seq.extract_channels(mappings[:,1])

        with open(self.local_filename, 'w') as f:
            f.write('#Writing pyNCS Connections')
            for i in range(n_connections):
                src_chip, dst_chip = nsetup.mon.extract_channels(mappings[i])
                src_neuron, src_core = nsetup.mon[src_chip].addrPhysicalExtract(mappings[i:i+1,0])
                fs, ei, dst_neuron, dst_core = nsetup.seq[dst_chip].addrPhysicalExtract(mappings[i:i+1,1])
                synapse = fs+(ei*2)
                s = 'U{:02d}-C{:02d}-N{:03d}->{:01d}-1-U{:02d}-C{:02d}-N{:03d}\n'.format( 
                    src_chip,
                    src_core[0],
                    src_neuron[0],
                    synapse[0], 
                    dst_chip,
                    dst_core[0], 
                    dst_neuron[0])
                f.write(s)
        
        self._commit()
        self.cur_mappings.append(mappings)
        return None



    @doc_inherit
    def set_mappings(self, mappings):
        self.clear_mappings()
        self.add_mappings(mappings)

#       dst_cores_1hot = sram_mappings[chipId, pre_srccore[conn2make],pre_addr[conn2make],1,:4]
#       dst_cores = np.sum([dst_cores_1hot[:,i]*2**i for i in range(4)], axis=0)

#       for d in np.unique(pre_srccore):
#           self.clear_sram_chip_core(chipId, d)

#       for d in np.unique(post_dstcore):
#           self.clear_cam_chip_core(chipId, d)


    def open(self):
        '''
        Open MapClient
        '''
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host,self.port))
        super(self.__class__, self).open()

    def close(self):
        '''
        Close MapClient
        '''
        self.client.close()
        del self.client
        super(self.__class__, self).close()

    @doc_inherit
    def get_mappings(self):
        return self.cur_table

    @doc_inherit
    def clear_mappings(self):
        self.cur_mappings = []
        return None

    @doc_inherit
    def clear_cam_chip_core(self, chipId, coreId):
        '''
        clear_cam_chip_core(self, chipId, coreId)
        Write zeros to all CAMs (deletes all connection in a core)
        '''
        #data =  clear_core_cam(chipId=chipId, coreId=coreId)
        print(('Clearing CAM on ChipID: {0} CoreID {1}'.format(chipId,coreId)))
        #self.commit(data)

        return None

    @doc_inherit
    def clear_sram_chip_core(self, chipId, coreId):
        #data = []
        #data.append(clear_sram_memory(chipId=chipId, sramId=1, coreId=coreId))
        #print(('Clearing SRAM on ChipID: {0} CoreID {1}'.format(chipId,coreId)))

        #self.commit(data)
        return None

    @contextmanager
    def _commit(self):
        '''
        '''
        import time, ftplib
        conf = None
        for chip in self.neurosetup.chips.values():
            if type(chip.configurator) == Configurator: 
                conf = chip.configurator 
        if conf is None:
            raise Exception('No Dynapse Chip Found\n')
        else:
            ftp = ftplib.FTP(self.host, user='pyncs')
            ftp.storlines('STOR {0}'.format(self.filename),
                    open('{0}'.format(self.local_filename),'r'))
            ftp.close()
            while conf.get_caer_sshs("/netparser/", "ProgramNetworkFrom.txt", 'bool').strip('\x00'.encode()) is "true":
                print(conf.get_caer_sshs("/netparser/", "ProgramNetworkFrom.txt", 'bool'))
                print("Waiting other processes to finish weight programming")
                time.sleep(.5)
            conf.set_caer_sshs("/netparser/", "net_txt_file", "string", self.remote_filename)
            time.sleep(.3)
            conf.set_caer_sshs("/netparser/", "ProgramNetworkFrom.txt", 'bool', "true")
            while conf.get_caer_sshs("/netparser/", "ProgramNetworkFrom.txt", 'bool').strip('\x00'.encode()) is "true":
                print("Waiting weight programming to complete")
                time.sleep(.5)
        
        
