#include "Neuron.h"
 
int main()
{
  std::cout << "Hello World!" << std::endl;
  ConnectionManager * manager = new ConnectionManager(0, 0);
  manager->PrintNeuronMap();
  ReadNetTXT(manager, "networks/hellonet.txt");

  manager->PrintNeuronMap();
  Neuron* ppre  = new Neuron(0, 0, 3);
  Neuron* ppost  = new Neuron(0, 0, 1);
  printf("Exists? %d \n", manager->ExistsConnection(ppre,ppost,3));

  if(manager->ExistsConnection(ppre, ppost, 3)){ 
    Synapse* syn = new Synapse(ppre, 3);
    Neuron* pre = manager->GetNeuron(ppre);
    Neuron* post = manager->GetNeuron(ppost);
    printf("next camid is %d\n", find_next_unused_cam(post->CAM));
    manager->DeleteConnection(syn, post);
  }

  ReadNetTXT(manager, "networks/mapping_table");
  ReadNetTXT(manager, "networks/mapping_table");
  manager->PrintNeuronMap();
  return 0;
}
