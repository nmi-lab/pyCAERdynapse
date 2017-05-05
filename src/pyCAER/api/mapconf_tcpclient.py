from pyNCSre.api.ConfAPI import MappingsBase
from contextlib import contextmanager
from pyCAER.utils import doc_inherit, getuser, flatten 
from pyCAER.maputils import * 
import numpy as np
import socket


class Mappings(MappingsBase):

    @doc_inherit
    def __init__(self, host='128.200.83.67', port=8890, debug=True, *args, **kwargs):
        self.host = host
        self.port = int(port)
        self.debug = debug
        self.sram_mappings = np.zeros([16,4,256,4,5],dtype='int32')
        self.cams_used = np.zeros([16,4,256],dtype='int32')
        self.cur_mappings = []
        self.clear_mappings()
        super(self.__class__, self).__init__()

    @doc_inherit
    def set_mappings(self, mappings):
        mappings = np.array(mappings, dtype='uint32')
        mon_chad = self.neurosetup.mon.addrPhysicalExtract(mappings[:,0])
        seq_chad = self.neurosetup.seq.addrPhysicalExtract(mappings[:,1])
        channels = [i for i,c in enumerate(mon_chad) if c is not None ] 
        assert len(channels) == 1, 'cross chip connections not yet supported'
        
        ch = channels[0]
        pre_addr, pre_srccore = mon_chad[ch]
        post_fs, post_ei, post_addr, post_dstcore = seq_chad[ch]

        if ch ==1:
            #Wordaround for chipId mismatch
            chipId = 0 
        else:
            chipId = ch


        sram_mappings = self.sram_mappings
        conn2make = np.nonzero(sram_mappings[chipId, pre_srccore, pre_addr, 1, post_dstcore]!=1)[0]
        sram_mappings[chipId, pre_srccore[conn2make],pre_addr[conn2make],1,post_dstcore[conn2make]]=1
        dst_cores_1hot = sram_mappings[chipId, pre_srccore[conn2make],pre_addr[conn2make],1,:4]
        dst_cores = np.sum([dst_cores_1hot[:,i]*2**(3-i) for i in range(4)], axis=0)

        for d in np.unique(pre_srccore):
            self.clear_sram_chip_core(chipId, d)

        for d in np.unique(post_dstcore):
            self.clear_cam_chip_core(chipId, d)

        data = []
        for i in conn2make:
            c = pre_srccore[i]
            n = pre_addr[i]
            d = dst_cores[i]
            bits = set_neurons_sram(chipId, coreId = c, sramId = 1, neurons = [n], destcoreId= d) 
            data.append(bits)

        for i in range(len(mappings)):
            n = post_addr[i]
            d = post_dstcore[i]
            if self.cams_used[chipId,d,n]<64:
                bits = set_neuron_cam(
                        chipId = chipId,
                        camId = self.cams_used[chipId,d,n],
                        ei = post_ei[i],
                        fs = post_fs[i],
                        srcneuronId = pre_addr[i],
                        destneuronId = n,
                        srccoreId = pre_srccore[i],
                        destcoreId = d)
                data.append(bits)
                self.cams_used[chipId,d,n]+=1
            else:
                print "exceeded CAM capacity on %d"%i
        
        self.commit(data)

        self.cur_mappings.append(mappings)


        return d


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
        self.sram_mappings[:,:,:,:,:] = -1
        self.cams_used[:,:,:] = 0
        self.cur_mappings = []
        return None

    @doc_inherit
    def clear_cam_chip_core(self, chipId, coreId):
        data =  clear_core_cam(chipId=chipId, coreId=coreId)
        print 'Clearing CAM on ChipID: {0} CoreID {0}'.format(chipId,coreId)
        self.commit(data)

        return None

    @doc_inherit
    def clear_sram_chip_core(self, chipId, coreId):
        data = []
        data.append(clear_sram_memory(chipId=chipId, sramId=1, coreId=coreId))
        data.append(clear_sram_memory(chipId=chipId, sramId=2, coreId=coreId))
        data.append(clear_sram_memory(chipId=chipId, sramId=3, coreId=coreId))
        print 'Clearing SRAM on ChipID: {0} CoreID {1}'.format(chipId,coreId)

        self.commit(data)
        return None

    @contextmanager
    def start_com(self):
        '''
        Context that opens the connection, initiates mapping configuration and closes the connections
        '''
        self.open()
        yield
        self.close()

    @contextmanager
    def commit(self, data):
        '''
        '''
        data = flatten(data) 
        with self.start_com():
            d=0
            while d<len(data):
                self.client.send(''.join(data[d:d+64]))
                d+=64
        if self.debug:
            print "Successfully written {0} connections".format(len(data))
        
        
