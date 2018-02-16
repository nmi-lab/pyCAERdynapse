//
// Created by rodrigo on 5/30/17.
//

//
// Contributed to by Emre Neftci and Andrew Hansen on 02/15/18
//

#include "Neuron.h"

using namespace std;

// Prototypes for function that needed them
//
//
Synapse::Synapse(Neuron* neuron_n, uint8_t connection_type_n):
        neuron(neuron_n),
        connection_type(connection_type_n),
        camid(255)
{
}

Synapse::Synapse(Neuron* neuron_n, uint8_t connection_type_n, uint8_t camid_n):
        neuron(neuron_n),
        connection_type(connection_type_n),
        camid(camid_n)
{
}

Neuron::Neuron(uint8_t chip_n ,uint8_t core_n ,uint8_t neuron_n):
        chip(chip_n),
        core(core_n),
        neuron(neuron_n)
{
    SRAM = vector<SRAM_cell>(0);
    CAM = vector<Synapse *>(0);
}

Neuron::Neuron():
        chip(0),
        core(0),
        neuron(0)
{
    SRAM = vector<SRAM_cell>(0);
    CAM = vector<Synapse *>(0);
}


SRAM_cell::SRAM_cell(Neuron * n):
        destinationChip(n->chip),
        destinationCores(0)
{
    connectedNeurons = vector<Neuron *>(0);
}

SRAM_cell::SRAM_cell():
        destinationChip(0),
        destinationCores(0)
{
    connectedNeurons = vector<Neuron *>(0);
}

string Neuron::GetLocString()const{
    stringstream ss;
    ss << 'U' << setw(2) << setfill('0') << unsigned(chip) << '-'
       << 'C' << setw(2) << setfill('0') << unsigned(core) << '-'
       << 'N' << setw(3) << setfill('0') << unsigned(neuron);
    return ss.str();
}

string Synapse::GetLocString()const{
    stringstream ss;
    ss << this->neuron->GetLocString();
    ss << '-' << 'S' << unsigned(connection_type);
    ss << '-' << 'C' << unsigned(camid);
    return ss.str();
}

void Neuron::Print() const {
    cout << GetLocString() << endl ;
}

void Synapse::Print() const {
    cout << GetLocString() << endl ;
}

// FIX

void Neuron::PrintSRAM() {
    if (this->SRAM.size() > 0) {
        for (vector<SRAM_cell>::iterator i = this->SRAM.begin(); i != this->SRAM.end(); ++i) {
            for(vector<Neuron *>::iterator j = i->connectedNeurons.begin(); j != i->connectedNeurons.end(); ++j){
                (*j)->Print();
            }
        }
    }else{
        cout << "empty SRAM" << endl;
    }
}


// This function returns a string containing the address of every destination neuron present in the SRAM of the specified neuron
// The string is like U00C00N001 U00C00N002 etc.
string Neuron::GetSRAMString() {
    stringstream ss;

    if (this->SRAM.size() > 0) {
        for (vector<SRAM_cell>::iterator i = this->SRAM.begin(); i != this->SRAM.end(); ++i) {
            for (vector<Neuron *>::iterator j = i->connectedNeurons.begin(); j != i->connectedNeurons.end(); ++j) {
                ss << (*j)->GetLocString() << " ";
            }
        }
    }else{
        ss << "empty SRAM";
    }
    return ss.str();
}

void Neuron::PrintCAM() {
    if (this->CAM.size() > 0) {
        for (vector<Synapse *>::iterator i = this->CAM.begin(); i != this->CAM.end(); ++i){
            (*i)->Print();
        }
    }else{
        cout << "empty CAM" <<endl;
    }
}

string Neuron::GetCAMString() {
    stringstream ss;

    if (this->CAM.size() > 0) {
        for (vector<Synapse *>::iterator camPtr = this->CAM.begin(); camPtr != this->CAM.end(); ++camPtr) {
            ss << (*camPtr)->GetLocString() << " ";
        }
    }else{
        ss << "empty CAM";
    }
    return ss.str();
}

vector<SRAM_cell>::iterator Neuron::FindEquivalentSram(Neuron * post){
  
    vector<SRAM_cell>::iterator sramPtr;
    for(sramPtr = this->SRAM.begin(); sramPtr != this->SRAM.end(); ++sramPtr){
        if(sramPtr->destinationChip == post->chip)
            break;
    }
    return sramPtr;
}

// A CAM clash happens when two neurons of different chips, but same address, are connected to the same destination core.
// Example: U0C0N1 -> U1C0N1 and U2C0N1 -> U1C0N2 create a CAM clash (same source neuron address C0N1)
// The predicate neuron n is the source neuron of the connection
// The CAMS inside the find_if belong to the destination neuron i want to check
// Of course every neuron of the destination core must be checked 
//TODO vector<Neuron *>::iterator Neuron::FindCamClash(Neuron * n){
//TODO     CamClashPred pred(n);
//TODO     return find_if(this->CAM.begin(), this->CAM.neuron.end(),pred);
//TODO }

//TODO CamClashPred::CamClashPred(Neuron* neuronA_) : neuronA_(neuronA_){}

// NeuronA_ is the source neuron of the connection
// NeuronB is a Neuron present inside the CAM of the destination neuron of the connection
//      (in other words is the sorce of another connection different from the one we are progamming).
// Note that NeuronB, as done in function FindCamClash, sweeps along all the neurons in the same CAM
// A CAMClash detection happens when there is a match of the neuron CAM address (determined by core and neuron value)
// *****BUT****** THE NEURONS MUST BELONG TO DIFFERENT CHIPS.
// Otherwise this simple allowed connection: U0C0N1 -> U0C1N1 and U0C0N1 -> U0C1N2 will create CAM clash
//TODO bool CamClashPred::operator()(const Neuron* neuronB){
//TODO     return (neuronA_->neuron == neuronB->neuron)&&(neuronA_->core == neuronB->core)&&(neuronA_->chip != neuronB->chip);
//TODO }

// Make neuron object comparable
bool operator < (const Neuron& x, const Neuron& y) {
    return tie(x.chip, x.core, x.neuron) < tie(y.chip, y.core, y.neuron);
}

bool operator > (const Neuron& x, const Neuron& y) {
    return tie(x.chip, x.core, x.neuron) > tie(y.chip, y.core, y.neuron);
}

bool operator == (const Neuron& x, const Neuron& y) {
    return tie(x.chip, x.core, x.neuron) == tie(y.chip, y.core, y.neuron);
}

bool operator == (const Synapse& x, const Synapse& y) {
    return tie(x.neuron->chip, x.neuron->core, x.neuron->neuron, x.connection_type) == tie(y.neuron->chip, y.neuron->core, y.neuron->neuron, y.connection_type);
}

bool ConnectionManager::ExistsConnection(Neuron *pre, Neuron *post, uint8_t connection_type){
  if ( neuronMap_.find(*pre) != neuronMap_.end() ) {
    pre = (neuronMap_.find(*pre)->second);
    if ( neuronMap_.find(*post) != neuronMap_.end() ) {
      post = (neuronMap_.find(*post)->second);
        Synapse * syn = new Synapse(pre, connection_type);
        for (vector<Synapse *>::iterator camPtr = post->CAM.begin(); camPtr != post->CAM.end(); ++camPtr) {
            //Check if Synapse Exists
            Synapse *exsyn = *camPtr; 
            if (*exsyn == *syn){
              return true;
            }
        }
        return false;
    } else { return false; }
  } else { return false; }

}

void ConnectionManager::find_connections_to_delete(){
      diffTable.clear();
      set_difference(
          currentTable.begin(), currentTable.end(),
          inputTable.begin(), inputTable.end(),
          inserter(diffTable, diffTable.begin())
          ); 

}

vector<uint8_t> ConnectionManager::CalculateBits(int chip_from, int chip_to){
    // TODO: Make programatic

    // We can also calculate programatically:
    // Program SRAM: {(South/North, steps x, West/East, steps y}
    // Direction: Assign 0->10, 1->00, 2->11, 3->01 and subtract with overflow
    // Ex: 3 - 1 = 01 - 10 = 01
    // Steps: Assign 0->00, 1->10, 2->01, 3->11 and add with overflow:
    // Ex: 3 + 1 = 11 + 10 = 01
    // Results, bit for 3->1 = d0 s0 d1 s1 = 0 0 1 1

    vector<uint8_t> bits;
    if (chip_from == 0){
        if (chip_to == 0){return bits = {0,0,0,0};}
        else if (chip_to == 1){return bits = {0,1,0,0};}
        else if (chip_to == 2){return bits = {0,0,1,1};}
        else if (chip_to == 3){return bits = {0,1,1,1};}
    }
    else if (chip_from == 1){
        if (chip_to == 0){return bits = {1,1,0,0};}
        else if (chip_to == 1){return bits = {0,0,0,0};}
        else if (chip_to == 2){return bits = {1,1,1,1};}
        else if (chip_to == 3){return bits = {0,0,1,1};}
    }
    else if (chip_from == 2){
        if (chip_to == 0){return bits = {0,0,0,1};}
        else if (chip_to == 1){return bits = {0,1,0,1};}
        else if (chip_to == 2){return bits = {0,0,0,0};}
        else if (chip_to == 3){return bits = {0,1,0,0};}
    }
    else if (chip_from == 3){
        if (chip_to == 0){return bits = {1,1,0,1};}
        else if (chip_to == 1){return bits = {0,0,0,1};}
        else if (chip_to == 2){return bits = {1,1,0,0};}
        else if (chip_to == 3){return bits = {0,0,0,0};}
    }
}

// For SRAM: Hot coded
uint16_t ConnectionManager::GetDestinationCore(int core){
    // TODO: Add ability to send to multiple cores
    if(core == 0){
        return 1;
    }
    else if(core == 1){
        return 2;
    }
    else if(core == 2){
        return 4;
    }
    else if(core == 3){
        return 8;
    }
    else{
        return 0;
    }
}

// For CAM
uint32_t ConnectionManager::NeuronCamAddress(int neuron, int core){
    return (uint32_t) neuron + core*256;
}

// The Connection manager keeps track of the SRAM and CAM registers of all neurons
// involved in a connection (sparse). Since there is no real way to access the
// registers themselves in order for this to work you must piping all connection settings through
// pipe all your connection settings through this manager (don't call caerDynapseWriteSram/Cam directly)
void ConnectionManager::DeleteConnection( Synapse * syn, Neuron * post){
        
        stringstream ss;
        string message;
        //Delete SRAM
        Neuron * pre = syn->neuron;
        vector<SRAM_cell>::iterator it = pre->FindEquivalentSram(post);
        if(it != pre->SRAM.end()){ // Found -> update SRAM Otherwise do nothing
            caerLog(CAER_LOG_DEBUG, __func__, "Similar connection");

            for (vector<Neuron *>::iterator cn = it->connectedNeurons.begin(); cn != it->connectedNeurons.end(); ++cn){
              if (*cn == post){
                cn = it->connectedNeurons.erase(cn);
                break;
              };
            }
            // update Destination core bits (OR between the current one and the post core ones)
            //Recalculate SRAM
            uint8_t oldDestCores = it->destinationCores;
            uint8_t newDestCores = 0;
            for(auto it2: it->connectedNeurons){
              newDestCores = newDestCores | GetDestinationCore(it2->core);
            }
            ss << "SRAM new: " << unsigned(newDestCores) << " old: " << unsigned(oldDestCores);
            caerLog(CAER_LOG_DEBUG, __func__, ss.str().c_str()); 
            if (unsigned(newDestCores) !=  unsigned(oldDestCores)) caerLog(CAER_LOG_DEBUG, __func__, "Rewriting SRAM"); 
            it->destinationCores = newDestCores;
            // Destination core already present
            //    program_sram = false;
            vector<uint8_t> dirBits = CalculateBits(pre->chip, it->destinationChip);
            uint16_t sramNumber = it - pre->SRAM.begin() + 1;
            string message = string("SRAM Settings: ") + 
            "U:" + to_string(pre->chip) + ", " +
            "C:" + to_string(pre->core) + ", " +
            "N:" + to_string(pre->neuron) + ", " +
            "C:" + to_string(pre->core) + ", " +
            "D0:" + to_string((bool)dirBits[0]) + ", " +
            "D1:" + to_string(dirBits[1]) + ", " +
            "D2:" + to_string((bool)dirBits[2])+ ", " +
            "D3:" + to_string(dirBits[3])+ ", " +
            "S:" + to_string(sramNumber) + "[" + to_string(pre->SRAM.size())+ "], " +
            "DB: " + to_string(it->destinationCores);

            caerLog(CAER_LOG_DEBUG, __func__, message.c_str());
         caerDeviceConfigSet(handle, DYNAPSE_CONFIG_CHIP, DYNAPSE_CONFIG_CHIP_ID, pre->chip);

         caerDynapseWriteSram(handle, pre->core, pre->neuron, pre->core, (bool)dirBits[0],
                          dirBits[1], (bool)dirBits[2], dirBits[3], (uint16_t) sramNumber, //first SRAM is for debbugging
                         it->destinationCores);

            caerLog(CAER_LOG_DEBUG, __func__, "Checking whether SRAM should be deleted");
            printf("%d \n,",it->connectedNeurons.size());

            if(it->connectedNeurons.size()==0){
              caerLog(CAER_LOG_DEBUG, __func__, "No more connected neurons. Deleting SRAM");
              it = pre->SRAM.erase(it);
            }  

        } else {
              caerLog(CAER_LOG_ERROR, __func__, "No valid SRAM found! Connection Table may be corrupted");
        }

        
        //Delete CAM
        bool erased = false;
        for (vector<Synapse *>::iterator camPtr = post->CAM.begin(); camPtr != post->CAM.end(); ++camPtr) {
            //Existing synapse
            Synapse *exsyn = *camPtr; 
            if (*exsyn == *syn){
              //printf("Found Synapse!\n");
              message = string("Deleting CAM Settings: ") + 
              "U:" + to_string(post->chip)+ ", " +
              "CAMN:" + to_string(exsyn->camid) + ", " +
              "PREADDR:" + to_string(NeuronCamAddress(exsyn->neuron->neuron,exsyn->neuron->core))+ ", " +
              "POSTADDR:" + to_string(NeuronCamAddress(post->neuron,post->core))+ ", " +
              "TYPE:" + to_string(exsyn->connection_type);

              caerLog(CAER_LOG_DEBUG, __func__, message.c_str());
              camPtr = post->CAM.erase(camPtr);
              caerDynapseWriteCam(handle, 0, NeuronCamAddress(post->neuron,post->core),
                          (uint32_t) exsyn->camid, exsyn->connection_type);
              //printf("erased!\n");
              erased = true;
              break;
            }
        }
        if(!erased){
              caerLog(CAER_LOG_ERROR, __func__, "No valid CAM found! Connection Table may be corrupted");
        }

}
void ConnectionManager::MakeConnection( Neuron * pre, Neuron * post, uint8_t cam_slots_number, uint8_t connection_type ){
    bool program_sram = true;
    bool program_cam = true;
    vector<SRAM_cell>::iterator it;

    // If the pre neuron has chip id 4 means that an input connection is specified (to the FPGA spike generator)
    // This means that only the CAM must be programmed, since the input event will be sent by the FPGA
    if(pre->chip == 4)
        program_sram = false;
    else{
    // Another case in which SRAM must not be programmed is when the destination neuron is in a core that is already 
    // addressed by at least one SRAM of the source neuron. In that case it is enough to program just the destination neuron CAM
    // In case the destination core is not the same, the SRAM destination core bits can be updated to reach the new core 
        
        // Find Sram whose destination chip is the same as post neuron   
        it = pre->FindEquivalentSram(post);
        if(it != pre->SRAM.end()){ // Found -> update SRAM
            caerLog(CAER_LOG_DEBUG, __func__, "Similar connection");
            it->connectedNeurons.push_back(post);

            // update Destination core bits (OR between the current one and the post core ones)
            uint8_t oldDestCores = it->destinationCores;
            it->destinationCores = oldDestCores | GetDestinationCore(post->core);
            if(oldDestCores == it->destinationCores) // Destination core already present
                program_sram = false;
        }
        else{ // Not found -> create new SRAM
            caerLog(CAER_LOG_DEBUG, __func__, "New SRAM will be programmed");

            // Create SRAM
            SRAM_cell * newSram = new SRAM_cell(post);
            newSram->destinationCores = GetDestinationCore(post->core); // Update destination core
            newSram->connectedNeurons.push_back(post); // Insert the connected neuron
            pre->SRAM.push_back(*newSram);

            // Go back with the pointer to the last element
            it = prev(pre->SRAM.end()); 
        }
    }

    if(program_sram == true){
        // In internal map

        vector<uint8_t> dirBits = CalculateBits(pre->chip, it->destinationChip);
        uint16_t sramNumber = it - pre->SRAM.begin() + 1;

        // print SRAM settings
        string message = string("SRAM Settings: ") + 
        "U:" + to_string(pre->chip) + ", " +
        "C:" + to_string(pre->core) + ", " +
        "N:" + to_string(pre->neuron) + ", " +
        "C:" + to_string(pre->core) + ", " +
        "D0:" + to_string((bool)dirBits[0]) + ", " +
        "D1:" + to_string(dirBits[1]) + ", " +
        "D2:" + to_string((bool)dirBits[2])+ ", " +
        "D3:" + to_string(dirBits[3])+ ", " +
        "S:" + to_string(sramNumber) + "[" + to_string(pre->SRAM.size())+ "], " +
        "DB: " + to_string(it->destinationCores);

        caerLog(CAER_LOG_DEBUG, __func__, message.c_str());

        // Program SRAM
         caerDeviceConfigSet(handle, DYNAPSE_CONFIG_CHIP, DYNAPSE_CONFIG_CHIP_ID, pre->chip);

         caerDynapseWriteSram(handle, pre->core, pre->neuron, pre->core, (bool)dirBits[0],
                            dirBits[1], (bool)dirBits[2], dirBits[3], (uint16_t) sramNumber, //first SRAM is for debbugging
                            it->destinationCores);
    }

    if(program_cam == true){
        // print CAM settings
        string message = string("CAM Settings: ") + 
        "U:" + to_string(post->chip)+ ", " +
        "CAMN:" + to_string(cam_slots_number)+ "[" + to_string(post->CAM.size())+ "], "
        "PREADDR:" + to_string(NeuronCamAddress(pre->neuron,pre->core))+ ", " +
        "POSTADDR:" + to_string(NeuronCamAddress(post->neuron,post->core))+ ", " +
        "TYPE:" + to_string(connection_type);

        caerLog(CAER_LOG_DEBUG, __func__, message.c_str());

        // Program CAM
        caerDeviceConfigSet(handle, DYNAPSE_CONFIG_CHIP, DYNAPSE_CONFIG_CHIP_ID, post->chip);

        // For each cam in cam_slot_num
        int curr_cam_size = post->CAM.size();
        uint8_t n = find_next_unused_cam(post->CAM);
        Synapse * syn = new Synapse(pre, connection_type, (uint8_t)(n));
        post->CAM.push_back(syn);
        caerLog(CAER_LOG_DEBUG, __func__, syn->GetLocString().c_str());
        caerDynapseWriteCam(
            handle,
            NeuronCamAddress(pre->neuron, pre->core),
            NeuronCamAddress(post->neuron,post->core),
            (uint32_t) n,
            connection_type);
    }
}

bool ConnectionManager::CheckAndConnect(Neuron * pre, Neuron * post, uint8_t cam_slots_number, uint8_t connection_type ){
    string message = string("Attempting to connect " + pre->GetLocString() + "-" + to_string(connection_type)
            + "-" + to_string(cam_slots_number) + "->" + post->GetLocString());
    caerLog(CAER_LOG_DEBUG, __func__, message.c_str());

    bool valid_connection = true;

    // Check if Neuron must be connected to itself (it was inserted but it is not required)
    /*if(*pre == *post) {
        message = "Cannot connect a neuron to itself";
        caerLog(CAER_LOG_NOTICE, __func__, message.c_str());
        valid_connection = false;
    }*/

    // If connection is still valid -> Check if synaptic type is valid
    if(valid_connection){
        if(connection_type < 0 & connection_type > 3){
            message = "Invalid Connection Type: " + connection_type;
            caerLog(CAER_LOG_DEBUG, __func__, message.c_str());
            valid_connection = false;
        }
    }

    // If connection is still valid -> Check if there are SRAM cell left
    // If they are all full, check if the connection require a new SRAM cell
    if(valid_connection){
        if (pre->SRAM.size() >= 3) {
            vector<SRAM_cell>::iterator it = pre->FindEquivalentSram(post);
            // If there are no similar connection, a new SRAM should be written, but it is full so cannot be done
            if (it == pre->SRAM.end()) {
                message = "SRAM Size Limit (3) Reached: " + pre->GetLocString();
                caerLog(CAER_LOG_NOTICE, __func__, message.c_str());
                valid_connection = false;
            }
        }
    }

    // If connection is still valid -> Check if there are CAM left
    if(valid_connection){
        if (cam_slots_number > 64 - post->CAM.size()) {
            message = "CAM Overflow for " + post->GetLocString() + ".\nCAM slot number requested (" + to_string(cam_slots_number)+ 
                        ") exceeds number of cam slot left (" + to_string(64 - post->CAM.size()) + ")";
            caerLog(CAER_LOG_NOTICE, __func__, message.c_str());
            valid_connection = false;
        }
    }

    // If connection is still valid -> Check for CAM Clash
    if(valid_connection){
//TODO         // Filter neuron map to get only neurons on the same chip and core of the destination neuron (were CAM clash could happen) 
//TODO         vector<Neuron*> filteredNeurons = FilterNeuronMap(post->chip, post->core);
//TODO         // Sweep over all the found neurons
//TODO         for(vector<Neuron *>::iterator neurit = filteredNeurons.begin(); neurit != filteredNeurons.end(); ++neurit){
//TODO             //find instances where contents in the cam will clash with the new element being added (same address as the source neuron)
//TODO             auto clashit = (*neurit)->FindCamClash(pre);
//TODO             //if clashes occour...just print the first one found (the other are implicit)
//TODO             if (clashit != (*neurit)->CAM.end()) {
//TODO                 message = string("CAM Clash at " + (*neurit)->GetLocString() + " between " + (*clashit)->GetLocString() + " and " + pre->GetLocString());
//TODO                 caerLog(CAER_LOG_NOTICE, __func__, message.c_str());
//TODO                 valid_connection = false;
//TODO                 break;
//TODO             }
//TODO         }
    }

    // If, at the end, the connection is still valid, do it
    if (valid_connection) {
        caerLog(CAER_LOG_DEBUG, __func__, "Passed tests");
        MakeConnection(pre, post, cam_slots_number, connection_type);
        return true;
    }

    return false;
}


ConnectionManager::ConnectionManager(caerDeviceHandle h, sshsNode n){
    handle = h;
    node = n;
}

map<Neuron,Neuron*> * ConnectionManager::GetNeuronMap(){
    return &(this->neuronMap_);
}

vector<Neuron*> ConnectionManager::FilterNeuronMap(uint8_t chip_n, uint8_t core_n){
    // Function that returns the neurons present in the map with a specific chip id and core id
    vector<Neuron *> filteredNeurons;
    Neuron * currNeuron;
    // Sweep the map and check for same chip id and core id
    for (map<Neuron,Neuron*>::iterator it=this->neuronMap_.begin(); it!=this->neuronMap_.end(); ++it){
        currNeuron = it->second;
        if((currNeuron->chip == chip_n) & (currNeuron->core == core_n))
            filteredNeurons.push_back(currNeuron);
    }
    return filteredNeurons;
}

void ConnectionManager::Clear(){
    caerLog(CAER_LOG_NOTICE, __func__,"Clearing Connection Manager...\nAll stored connections will be deleted");
    this->neuronMap_.clear();
}


stringstream ConnectionManager::GetNeuronMapString(){
    stringstream ss;
    
    for(auto it = neuronMap_.cbegin(); it != neuronMap_.cend(); ++it)
    {
        Neuron * entry = it->second; 
        ss << "\n";
        ss << entry->GetLocString() << 
        " -- SRAM: " << entry->GetSRAMString() <<
        " -- CAM: " << entry->GetCAMString();  
    }

    return ss;
}

void ConnectionManager::PrintNeuronMap(){   

    string entry_message;
    
    for(auto it = neuronMap_.cbegin(); it != neuronMap_.cend(); ++it)
    {
        Neuron * entry = it->second; 
        entry_message = "\n\n"+ 
        entry->GetLocString() + 
        " -- SRAM: " + 
        entry->GetSRAMString() +
        " -- CAM: " + 
        entry->GetCAMString();

        caerLog(CAER_LOG_NOTICE, __func__, entry_message.c_str());
    }
}

Neuron * ConnectionManager::GetNeuron(Neuron * pre){
    return neuronMap_.find(*pre)->second;
}

void ConnectionManager::Connect(Neuron * pre, Neuron * post, uint8_t cam_slots_number, uint8_t connection_type){

    // If already instanciated neuron, use that, otherwise make new entry
    if ( neuronMap_.find(*pre) == neuronMap_.end() ) {
        // New neuron, include in map
        neuronMap_[*pre] = pre;
    } else {
        // Already instantiated, delete and re-reference
        //delete pre;
        pre = neuronMap_[*pre];
    }
    if ( neuronMap_.find(*post) == neuronMap_.end() ) {
        // New neuron, include in map
        neuronMap_[*post] = post;
    } else {
        // Already instantiated, delete and re-reference
        //delete post;
        post = neuronMap_[*post];
    }

    // Attempt to connect
    try{
        if(CheckAndConnect(pre, post, cam_slots_number, connection_type)){
            string message = string("+++ Connected " + pre->GetLocString() + "-" + to_string(connection_type) +
            "-" + to_string(cam_slots_number) + "->" + post->GetLocString()+ "\n");
        caerLog(CAER_LOG_DEBUG, __func__, message.c_str());
        } else{
             string message = string("XXX Did not connect " + pre->GetLocString() + "-" + to_string(connection_type) +
            "-" + to_string(cam_slots_number) + "->" + post->GetLocString()+ "\n");
        caerLog(CAER_LOG_NOTICE, __func__, message.c_str());
        }        
    }
    catch (const string e){
        caerLog(CAER_LOG_NOTICE, __func__, e.c_str());
    }

}

void ConnectionManager::SetBias(uint8_t chip_n ,uint8_t core_n , const char *biasName, uint8_t coarse_value, uint8_t fine_value, bool high_low){
    string message = string("Setting bias ") +
                     string(biasName) + " to value " +
                     to_string(coarse_value) + "," + to_string(fine_value) + " U/D = " +
                     to_string(high_low);
    caerLog(CAER_LOG_DEBUG, __func__, message.c_str());

    try{
         caerDeviceConfigSet(handle, DYNAPSE_CONFIG_CHIP, DYNAPSE_CONFIG_CHIP_ID, U32T(chip_n));
         caerDynapseSetBiasCore(node, chip_n, core_n, biasName, coarse_value, fine_value, high_low);
    }
    catch (const string e){
        caerLog(CAER_LOG_NOTICE, __func__, e.c_str());
    }
}

void ConnectionManager::SetTau2(uint8_t chip_n ,uint8_t core_n, uint8_t neuron_n){
    // Function that set the tau2 for a specific neuron
    string message = string("Setting tau2 of neuron ") +
                     "U:" + to_string(chip_n) + ", " +
                     "C:" + to_string(core_n) + ", " +
                     "N:" + to_string(neuron_n);
    caerLog(CAER_LOG_DEBUG, __func__, message.c_str());
    try{
         caerDeviceConfigSet(handle, DYNAPSE_CONFIG_CHIP, DYNAPSE_CONFIG_CHIP_ID, chip_n); // Select the chip
         caerDeviceConfigSet(handle, DYNAPSE_CONFIG_TAU2_SET, core_n, neuron_n); // Set tau2 for a specific neuron
    }
    catch (const string e){
        caerLog(CAER_LOG_NOTICE, __func__, e.c_str());
    }
}

bool ReadNetTXT (ConnectionManager * manager, string filepath) {

//CURRENT////////////////////////////////////////////////////////////////////////////////////////////////////CURRENT//
	// Creates a static vector to hold current connections
	static vector< vector<int> > connectionTable;
	static vector< vector<int> > bufferTable;
//CURRENT////////////////////////////////////////////////////////////////////////////////////////////////////CURRENT//

	// If no current connections (ClearCAM was previously called, initialize currentConnections with incoming user input from .txt)
	//if (connectionTable.empty() == true) {
	// fill with incoming connections (currently buffered via bufferTable)
		connectionTable = bufferTable;
	//}

    caerLog(CAER_LOG_DEBUG, __func__, ("attempting to read net found at: " + filepath).c_str());
    ifstream netFile (filepath);
    string connection;
    if (netFile.is_open())
    {
        caerLog(CAER_LOG_NOTICE, __func__, ("parsing net found at: " + filepath).c_str());
        vector<uint8_t > cv;
        while ( getline (netFile, connection) )
        {
            if(!connection.empty()){
                // Ignore comments (#)
                if(connection[0] != '#'){
                    size_t prev = 0, pos;
                    // Expected structure is:
                    //     pre_addrss   -cam_slots_number   ->  post_addrss 
                    // ex: U00-C01-N001 -32                 ->  U02-C01-N001 
                    // without tabs: U00-C01-N001-32->U02-C01-N001
                    while ((pos = connection.find_first_of("UCN->", prev)) != string::npos)
                    {
                        if (pos > prev)
                            cv.push_back((unsigned char &&) stoi(connection.substr(prev, pos - prev)));
                        prev = pos+1;
                    }

                    if (prev < connection.length())
                        cv.push_back((unsigned char &&) stoi(connection.substr(prev, string::npos)));
                    if (cv[4]>1){
                      caerLog(CAER_LOG_ERROR, __func__, "cams_slot_number>1 is forbidden: ");
                      cv[4]=1;

                    }

                    //manager->ExistsConnection(new Neuron(cv[0],cv[1],cv[2]),new Neuron(cv[5],cv[6],cv[7]),cv[3])
                    Neuron * ppre = new Neuron(cv[0],cv[1],cv[2]);
                    Neuron * ppost = new Neuron(cv[5],cv[6],cv[7]);
                    
                    vector<int> currentConnection;
                    for (int i=0; i<cv.size(); i++) {
                      currentConnection.push_back(static_cast<int>(cv[i]));
                    }
                    manager->inputTable.push_back(currentConnection);
                    currentConnection.clear();

                    //Add non-existing connections
                    if(!manager->ExistsConnection(ppre,ppost,cv[3])){ 
                    manager->Connect(ppre,ppost,cv[4],cv[3]);
                    } else {
                      caerLog(CAER_LOG_NOTICE, __func__, "Connection Already Exists");
                    }
                    cv.clear();


                } else{
                    // Print comments in network file that start with #! for debbuging
                    if(connection[1] == '!'){
                        caerLog(CAER_LOG_NOTICE, __func__, ("Printing comment: " + connection + "\n").c_str());
                    }
                }
            }
        }
        netFile.close();

        //printf("Number of differences %d %d %d\n", manager->diffTable.size(), manager->inputTable.size(), manager->currentTable.size());
        manager->find_connections_to_delete();

        //printf("Number of differences %d\n", manager->diffTable.size());
        for(auto icv = manager->diffTable.begin();
            icv != manager->diffTable.end();
            ++icv){

        string message = "CV VALUE IS THIS: "; 
        caerLog(CAER_LOG_DEBUG, __func__, message.c_str());
        //printf("%d %d %d %d \n",(*icv)[0],(*icv)[1],(*icv)[2],(*icv)[3]);
        //printf("%d %d %d\n",(*icv)[5],(*icv)[6],(*icv)[7]);

        Neuron * ppre = new Neuron((*icv)[0],(*icv)[1],(*icv)[2]);
        Neuron * ppost = new Neuron((*icv)[5],(*icv)[6],(*icv)[7]);
        if(manager->ExistsConnection(ppre,ppost, (*icv)[3])){ 
          Neuron* pre = manager->GetNeuron(ppre);
          Synapse* syn = new Synapse(pre, (*icv)[3]);
          Neuron* post = manager->GetNeuron(ppost);
          manager->DeleteConnection(syn, post);
        }


        }

        for(auto icv = manager->diffTable.begin();
            icv != manager->diffTable.end();
            ++icv){

        string message = "CV VALUE IS THIS: "; 
        caerLog(CAER_LOG_DEBUG, __func__, message.c_str());
        //printf("%d %d %d %d \n",(*icv)[0],(*icv)[1],(*icv)[2],(*icv)[3]);
        //printf("%d %d %d\n",(*icv)[5],(*icv)[6],(*icv)[7]);

        Neuron * ppre = new Neuron((*icv)[0],(*icv)[1],(*icv)[2]);
        Neuron * ppost = new Neuron((*icv)[5],(*icv)[6],(*icv)[7]);
        if(manager->ExistsConnection(ppre,ppost, (*icv)[3])){ 
          caerLog(CAER_LOG_ERROR, __func__, "Connection still exists!\n");
          Neuron* pre = manager->GetNeuron(ppre);
          Synapse* syn = new Synapse(pre, (*icv)[3]);
          Neuron* post = manager->GetNeuron(ppost);
          manager->DeleteConnection(syn, post);
        }


        }


        manager->currentTable.clear();
        manager->currentTable = manager->inputTable;
        manager->inputTable.clear();
        manager->diffTable.clear();
        return true;        

    }
    else{
        caerLog(CAER_LOG_ERROR, __func__, ("Unable to open file: " + filepath).c_str());  
        return false;
    } 


}

// TODO: Finish XML reader
bool ReadNetXML (ConnectionManager * manager, string filepath) {

    FILE *netFile;
    mxml_node_t *tree;
    string message = "";
    bool correct_input = true;

    caerLog(CAER_LOG_DEBUG, __func__, ("opening file: " + filepath).c_str());
    netFile = fopen(filepath.c_str(), "r");

    if (netFile == NULL){
        caerLog(CAER_LOG_ERROR, __func__, ("unable to open file: " + filepath).c_str());
        return false;
    }
  

    tree = mxmlLoadFile(NULL, netFile, MXML_NO_CALLBACK);

    if (tree == NULL){
        caerLog(CAER_LOG_ERROR, __func__, ("Invalid XML file"));
        return false;
    }

    const char *name = mxmlGetElement(tree);
    //size_t level = 0;
    caerLog(CAER_LOG_DEBUG, __func__, (name));

    mxml_node_t *connections;
    connections = mxmlFindElement(tree, tree, "CONNECTIONS", NULL, NULL, MXML_DESCEND);


    mxml_node_t *current_connection = mxmlGetFirstChild(connections);
    mxml_node_t *pre;
    mxml_node_t *post;

    current_connection = mxmlGetNextSibling(current_connection);

    while (name != NULL){

        message = "";
        correct_input = true;
        
        auto connection_type = (uint8_t)atoi(mxmlElementGetAttr(current_connection, "connection_type"));
       
        
        if (connection_type < 0 || connection_type > 3){ 
            message = string(message + "Connection Type out of range (0-3): " + to_string(connection_type) + "\n");
            correct_input = false;
        }
        
        auto cam_slots_number = (uint8_t)atoi(mxmlElementGetAttr(current_connection, "cam_slots_number"));
       
        if (cam_slots_number < 0 || cam_slots_number > 64){ 
            message = string(message + "CAM slot number out of range (0-64): " + to_string(cam_slots_number) + "\n");
            correct_input = false;
        }

       
        pre = mxmlFindElement(current_connection, current_connection, "PRE", NULL, NULL, MXML_DESCEND);
        if (pre == NULL){ 
            message = string(message + "Each connection should have a PRE neuron children\n");
            correct_input = false;
        }

        auto pre_chip = (uint8_t)atoi(mxmlElementGetAttr(pre, "CHIP"));
        if (pre_chip < 0 || pre_chip > 3){ 
            message = string(message + "Pre-Synaptic chip out of range (0-3): " + to_string(pre_chip)+ "\n");
            correct_input = false;
        }


        auto pre_core = (uint8_t)atoi(mxmlElementGetAttr(pre, "CORE"));
        if (pre_core < 0 || pre_core > 3){ 
            message = string(message + "Pre-Synaptic core out of range (0-3): " + to_string(pre_core)+ "\n");
            correct_input = false;
        }

        auto pre_neuron = (uint8_t)atoi(mxmlElementGetAttr(pre, "NEURON"));
        if (pre_neuron < 0 || pre_neuron > 255){ 
            message = string(message + "Pre-Synaptic neuron out of range (0-255): " + to_string(pre_neuron)+ "\n");
            correct_input = false;
        }

        post = mxmlFindElement(current_connection, current_connection, "POST", NULL, NULL, MXML_DESCEND);

        auto post_chip = (uint8_t)atoi(mxmlElementGetAttr(post, "CHIP"));
        if (post_chip < 0 || post_chip > 3){ 
            message = string(message + "Post-Synaptic chip out of range (0-3): " + to_string(post_chip)+ "\n");
            correct_input = false;
        }


        auto post_core = (uint8_t)atoi(mxmlElementGetAttr(post, "CORE"));
        if (post_core < 0 || post_core > 3){ 
            message = string(message + "Post-Synaptic core out of range (0-3): " + to_string(post_core)+ "\n");
            correct_input = false;
        }

        auto post_neuron = (uint8_t)atoi(mxmlElementGetAttr(post, "NEURON"));
        if (post_neuron < 0 || post_neuron > 255){ 
            message = string(message + "Post-Synaptic neuron out of range (0-255): " + to_string(post_neuron)+ "\n");
            correct_input = false;
        }

        
        // Make connection
        if(correct_input){
              manager->Connect(
              new Neuron(pre_chip, pre_core, pre_neuron),
              new Neuron(post_chip, post_core, post_neuron),
              cam_slots_number, connection_type);
          }
          else{
               caerLog(CAER_LOG_NOTICE, __func__, string("Incorrect Input: " + message).c_str());
        }
       

        // Loop to next connection 
        // TODO: figure out why I have to do this twice
        current_connection = mxmlGetNextSibling(current_connection);
        current_connection = mxmlGetNextSibling(current_connection);
        name = mxmlGetElement(current_connection);
    }

    fclose(netFile);

}

bool ReadBiasesTauTXT (ConnectionManager * manager, string filepath) {

    caerLog(CAER_LOG_DEBUG, __func__, ("attempting to read net found at: " + filepath).c_str());
    ifstream netFile (filepath);
    string bias_tau;
    if (netFile.is_open())
    {
        caerLog(CAER_LOG_NOTICE, __func__, ("parsing biases found at: " + filepath).c_str());
        vector<string > cv;
        vector<uint8_t> cv_int;
        while ( getline (netFile, bias_tau) )
        {
            if(!bias_tau.empty()){
                // Ignore comments (#)
                if(bias_tau[0] != '#'){
                    size_t prev = 0, pos;
                    // Expected structure is:
                    // FOR BIAS
                    //     core_addr   -bias_name    -coarse_value   -fine_value   -High/Low current 
                    // ex: U00-C00     -IF_AHTAU_N   -7              -34           -true 
                    // without tabs: U00-C00-IF_AHTAU_N-7-34-true

                    // FOR TAU
                    //     neur_addr     -TAU2
                    // ex: U00-C00-N001  -TAU2
                    // without tabs: U00-C00-N001-TAU2

                    // Separate all parts of the parsed line, using as separator "-" 

                    while ((pos = bias_tau.find_first_of("-", prev)) != string::npos)
                    {
                        if (pos > prev)
                            cv.push_back(bias_tau.substr(prev, pos - prev));
                        prev = pos+1;
                    }
                    // Add last element
                    if (prev < bias_tau.length())
                        cv.push_back(bias_tau.substr(prev, string::npos));

                    //string message = "CV VALUE IS THIS: " + cv[0] + "," + cv[1] + "," + cv[2] + "," + cv[3] + "," + cv[4] + "," + cv[5]; 
                    //caerLog(CAER_LOG_DEBUG, __func__, message.c_str());

                    // Convert Chip and Core id in int   
                    cv_int.push_back((unsigned char &&) stoi(cv[0].substr(1, string::npos)));
                    cv_int.push_back((unsigned char &&) stoi(cv[1].substr(1, string::npos)));

                    // If TAU has to been set, complete the parsing in a certain way
                    if(cv[3].compare(string("TAU2")) == 0){
                        cv_int.push_back((unsigned char &&) stoi(cv[2].substr(1, string::npos))); // Neuron index
                        manager->SetTau2(cv_int[0], cv_int[1], cv_int[2]);
                    }
                    // If a BIAS has to be set, complete the parsing in a different way
                    else {
                        cv_int.push_back((unsigned char &&) stoi(cv[3])); // coarse value
                        cv_int.push_back((unsigned char &&) stoi(cv[4])); // fine value
                        if(cv[5].compare(string("true")) == 0) // High current
                            cv_int.push_back((unsigned char &&) 1); 
                        else // Low current
                            cv_int.push_back((unsigned char &&) 0);
                        manager->SetBias(cv_int[0], cv_int[1], cv[2].c_str(), cv_int[2], cv_int[3], bool(cv_int[4]));
                    }

                    cv.clear();
                    cv_int.clear();
                } else{
                    // Print comments in network file that start with #! for debbuging
                    if(bias_tau[1] == '!'){
                        caerLog(CAER_LOG_NOTICE, __func__, ("Printing comment: " + bias_tau + "\n").c_str());
                    }
                }
            }
        }
        netFile.close();
        return true;        

    }
    else{
        caerLog(CAER_LOG_ERROR, __func__, ("unable to open file: " + filepath).c_str());  
        return false;
    } 
}

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
