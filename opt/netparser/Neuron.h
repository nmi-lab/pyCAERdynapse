//
// Created by rodrigo on 5/30/17.
//

#ifndef CAER_NEURON_H
#define CAER_NEURON_H

#endif //CAER_NEURON_H

//
// Created by rodrigo on 5/30/17.
//

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
//TEST #include <libcaer/devices/dynapse.h>
//TEST #include "modules/ini/dynapse_utils.h"
//TEST #include "base/mainloop.h"
//
// Following code to use this code in standalone mode
#include "testcaer.h"

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

uint8_t find_next_unused_cam(vector<Synapse *> CAM){
      vector<uint8_t> v1 (0);
      //64 CAMs per neuron
      for( uint8_t i = 0; i <= 64; i++ ) v1.push_back( i );

      vector<uint8_t> v2 (0);
      for(auto i: CAM) v2.push_back( (*i).camid );

      vector<uint8_t> diff;

      //DEBUG      for (auto i : v1) std::cout << unsigned(i) << ' ';
      //DEBUG      std::cout << "minus ";
      //DEBUG      for (auto i : v2) std::cout << unsigned(i) << ' ';
      //DEBUG      std::cout << "is: ";

      set_difference(v1.begin(), v1.end(), v2.begin(), v2.end(), 
                        inserter(diff, diff.begin())); 

      //DEBUG for (auto i : diff) std::cout << unsigned(i) << ' ';
      //DEBUG std::cout << '\n';
      return diff.front();
}

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

    const uint8_t destinationChip;
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

    bool ExistsConnection(Neuron *pre, Neuron *post, uint8_t connection_type);
    
    void Clear();

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
