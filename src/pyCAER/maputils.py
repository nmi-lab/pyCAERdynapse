import numpy as np

def clear_sram_memory(sramId = 1, coreId = 0, chipId = 0):
    bits = []
    for neuronId in range(256):
        #we loop over all cores
        dx = 0;
        sx = 0;
        dy = 0;
        sy = 0;
        destcoreId = 0;  #one hot coded    
        bits.append(neuronId << 7 | sramId << 5 | coreId << 15 | 1 << 17 | 1 << 4 | destcoreId << 18 | sy << 27 | dy << 25 | dx << 22 | sx << 24 | coreId << 28 | chipId <<30);
    return np.array(bits).astype('uint64').tostring()

def set_neurons_sram(
        chipId,
        coreId,
        sramId = 1,
        neurons = list(range(256)),
        destcoreId = 0,
        dx = 0,
        sx = 0,
        dy = 0,
        sy = 0,
        ):

    if hasattr(destcoreId, '__len__'):
        destcoreId = sum([2**i for i in destcoreId])

    bits = []
    for neuronId in neurons:
        #we loop over all cores
        bits.append( neuronId << 7 | sramId << 5 | coreId << 15 | 1 << 17 | 1 << 4 | destcoreId << 18 | sy << 27 | dy << 25 | dx << 22 | sx << 24 | coreId << 28 | chipId <<30)
    return np.array(bits).astype('uint64').tostring()

def clear_camId(
        chipId,
        coreId,
        camId,
        neuronId = 0):
    bits = chipId << 30 | 1 << 17 |coreId << 15 | neuronId<<5 ;
    return np.array(bits).astype('uint64').tostring()

def clear_core_cam( chipId,
                    coreId,
                    ):
    bits = []
    for row in range(1024):
        for col in range(16):
            bits.append(chipId << 30 | 1 << 17 |coreId << 15 | row <<5 | col );
    return np.array(bits).astype('uint64').tostring()

def set_neuron_cam(
        chipId,
        camId,
        ei = 1, #excitatory
        fs = 1, #fast
        srcneuronId = 0, #sending neuron
        destneuronId = 0, #receiving neuron
        srccoreId = 0, #sending core (= extratag)
        destcoreId = 0): #receiving core (not 1 hot coded)
    bits = []
    synapse_row = camId;                 # cam ID
    nrn_1 = (destneuronId & 0xf0)>>4
    nrn_2 = destneuronId & 0x0f
    bits .append( chipId << 30 | ei << 29 | fs << 28 | srcneuronId << 20 | srccoreId << 18 | 1 << 17 | destcoreId << 15 | nrn_1 << 11 | camId << 5 | nrn_2 );
    return np.array(bits).astype('uint64').tostring()

def tau1_core_set(chipId,coreId):
    bits = chipId << 30 |\
            1 << 12 |\
            0 << 11 |\
            coreId << 8
    return np.array(bits).astype('uint64').tostring()

def tau2_core_set(chipId,coreId):
    bits = chipId << 30 |\
            1 << 12 |\
            1 << 11 |\
            coreId << 8
    return np.array(bits).astype('uint64').tostring()

def tau2_set(chipId,coreId,neuronId):
    bits = chipId << 30 |\
            1 << 10 |\
            coreId << 8 |\
            neuronId
    return np.array(bits).astype('uint64').tostring()
