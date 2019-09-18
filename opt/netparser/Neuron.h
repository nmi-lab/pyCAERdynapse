//
// Created by rodrigo on 5/30/17.
//

//
// Contributed to by Emre Neftci and Andrew Hansen on 02/15/18
//

#ifndef CAER_NEURON_H
#define CAER_NEURON_H

#endif //CAER_NEURON_H

#include <algorithm>    // std::find_if
#include <iostream>
#include <map>
#include <vector>
#include <iomanip>
#include <string>
#include <sstream>
#include <functional>
#include <set>
#include <fstream>
#include <mxml.h>
#include <libcaer/devices/dynapse.h>
#include "modules/ini/dynapse_utils.h"
#include "base/mainloop.h"
//
// Following code to use this code in standalone mode
//#include "testcaer.h"

using namespace std;

struct SRAM_cell;

struct Neuron; 

struct Synapse {
    Neuron * neuron;
    uint8_t connection_type;
    uint8_t camid;
    Synapse(Neuron* neuron_n, uint8_t connection_type_n);
    Synapse(Neuron* neuron_n, uint8_t connection_type_n, uint8_t camid_n);
    string GetLocString() const;
    void Print() const;
};

uint8_t find_next_unused_cam(vector<Synapse *> CAM);

struct Neuron {
    const uint8_t chip;
    const uint8_t core;
    const uint8_t neuron;
    vector<SRAM_cell> SRAM;
    vector<Synapse *> CAM;
    map< string, uint8_t > CAMmap;

    Neuron(uint8_t chip_n ,uint8_t core_n ,uint8_t neuron_n);
    Neuron();
    string GetLocString() const;
    void Print() const;
    void PrintSRAM();
    void PrintCAM();
    string GetSRAMString();
    string GetCAMString();
    string GetCAMmapString();
    vector<SRAM_cell>::iterator FindEquivalentSram(Neuron * post);
    vector<Neuron *>::iterator FindCamClash(Neuron * n);
};

struct SRAM_cell{
    SRAM_cell(Neuron* n);
    SRAM_cell();

    uint8_t destinationChip;
    uint8_t destinationCores;
    vector<Neuron *> connectedNeurons;
};

//TODO class CamClashPred{
//TODO private:
//TODO     Neuron* neuronA_;
//TODO public:
//TODO     CamClashPred(Neuron* neuronA_);
//TODO     bool operator()(const Neuron* neuronB);
//TODO };

// Make neuron object comparable
bool operator < (const Neuron& x, const Neuron& y) ;
bool operator > (const Neuron& x, const Neuron& y) ;
bool operator == (const Neuron& x, const Neuron& y) ;
bool operator == (const Synapse& x, const Synapse& y) ;

// Class that manages all connections
class ConnectionManager {
private:

    map< Neuron, Neuron* > neuronMap_;
    caerDeviceHandle handle;
    sshsNode node;

    // Hard coded bit vectors for SRAM connections and destination cores
    vector<uint8_t> CalculateBits(int chip_from, int chip_to);
    uint16_t GetDestinationCore(int core);

    // For CAM
    uint32_t NeuronCamAddress(int neuron, int core);

    // Checks for valid connection and calls MakeConnection
    bool CheckAndConnect(Neuron *pre, Neuron *post, uint8_t syn_strength, uint8_t connection_type);

    // Appends connection to software SRAM and CAM and calls caerDynapseWriteSram and caerDynapseWriteCam
    void MakeConnection(Neuron *pre, Neuron *post, uint8_t syn_strength, uint8_t connection_type);


public:
    ConnectionManager(caerDeviceHandle h, sshsNode n);
    void DeleteConnection(Synapse * syn, Neuron * post);

    void find_connections_to_delete();

    bool ExistsConnection(Neuron *pre, Neuron *post, uint8_t connection_type);
    
    void Clear();

    vector<vector<int> > currentTable;
    vector<vector<int> > inputTable;
    vector<vector<int> > diffTable;

    map<Neuron, Neuron *> *GetNeuronMap();
    vector<Neuron*> FilterNeuronMap(uint8_t chip_n, uint8_t core_n);
    void PrintNeuronMap();
    stringstream GetNeuronMapString();

    Neuron * GetNeuron(Neuron *pre);

    // Checks for valid connection and calls MakeConnection
    // TODO: Implement syn_strength and connection type
    void Connect(Neuron *pre, Neuron *post, uint8_t syn_strength, uint8_t connection_type);
    void SetBias(uint8_t chip_id, uint8_t core_id, const char *biasName, uint8_t coarse_value, uint8_t fine_value, bool highLow);
    void SetTau2(uint8_t chip_n ,uint8_t core_n, uint8_t neuron_n);
};

// Reads net from txt file in format U02-C02-N002->U02-C02-N006
bool ReadNetTXT (ConnectionManager * manager, string filepath) ;

bool ReadNetXML (ConnectionManager * manager, string filepath) ;

// Reads net from txt file in format U00-C00-IF_AHTAU_N-7-34-true
bool ReadBiasesTauTXT (ConnectionManager * manager, string filepath) ;
