#include "Neuron.h"
 
int main()
{
  std::cout << "Hello World!" << std::endl;
  ConnectionManager * manager = new ConnectionManager(0, 0);
  manager->PrintNeuronMap();

//  manager->PrintNeuronMap();
//  Neuron* ppre  = new Neuron(0, 0, 3);
//  Neuron* ppost  = new Neuron(0, 0, 1);
//  printf("Exists? %d \n", manager->ExistsConnection(ppre,ppost,3));
//
//  if(manager->ExistsConnection(ppre, ppost, 3)){ 
//    Neuron* pre = manager->GetNeuron(ppre);
//    Synapse* syn = new Synapse(pre, 3);
//    Neuron* post = manager->GetNeuron(ppost);
//    printf("next camid is %d\n", find_next_unused_cam(post->CAM));
//    manager->DeleteConnection(syn, post);
//  }


  ReadNetTXT(manager, "networks/mapping_table");
  manager->PrintNeuronMap();
  ReadNetTXT(manager, "networks/mapping_table_half");
  manager->PrintNeuronMap();
  ReadNetTXT(manager, "networks/mapping_table");
  manager->PrintNeuronMap();

//  if(manager->ExistsConnection(ppre, ppost, 3)){ 
//    Neuron* pre = manager->GetNeuron(ppre);
//    Synapse* syn = new Synapse(pre, 3);
//    Neuron* post = manager->GetNeuron(ppost);
//    printf("next camid is %d\n", find_next_unused_cam(post->CAM));
//    manager->DeleteConnection(syn, post);
//  }

  return 0;
}
