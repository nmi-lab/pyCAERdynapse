from lxml import etree as ET

filename = 'hellonet.xml'
cam_slot_number = 16

Connections = ET.Element('CONNECTIONS')

chips = [1,2,3]
cores = [0,1,2]
neurons = range(256)

for chip in chips:
        for neuron in neurons:
            New_Connection = ET.SubElement(Connections,'CONNECTION', 
                attrib={
                "cam_slots_number":"16", 
                "connection_type":str(chip)
                })

            PRE = ET.SubElement(New_Connection,'PRE', {
                'CHIP':str(chip), 
                'CORE':str(chip), 
                'NEURON':str(neuron)
                })

            POST = ET.SubElement(New_Connection,'POST', {
                'CHIP':"0", 
                'CORE':"0", 
                'NEURON':str(neuron)
                })

tree = ET.ElementTree(Connections)
tree.write(filename, pretty_print=True, xml_declaration=True, encoding="utf-8")
print('Network written to {}'.format(filename))