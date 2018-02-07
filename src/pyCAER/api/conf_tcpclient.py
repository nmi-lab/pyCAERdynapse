# api file for pyNCS conf
# import base classes from pyNCS
from pyNCSre.api.ConfAPI import ConfiguratorBase
from pyNCSre import doc_inherit #for inheriting documentation from base classes
from pyCAER import caer_communication
from lxml import etree

class Parameter:
    def __init__(self, name, path):
        '''
        Parameter(parameters, configurator)
        params_dict: dictionary of parameters and values
        This object is designed to be used with the configurator to set parameters
        '''
        self.path = path
        self.SignalName = name
        self.attr = {}

    def add_attr(self, masterkey, attrdict, value = None):
        self.attr[masterkey] = ParameterAttribute(attrdict, value)

    def __str__(self):
        return str([str(s)+' ' for s in self.attr])

    def __repr__(self):
        return str([str(s)+' ' for s in self.attr])

class ParameterAttribute:
    def __init__(self, attrdict, value):
        self.data = attrdict
        self.value = value

    def __str__(self):
        return str(self.data)



class Configurator(ConfiguratorBase):
    def __init__(self, host='localhost', port=4040):
        '''
        Configuration class to set biases through the AMDA boards designed at the Institute of Neuroinformatics.
        Input:
        *host:* hostname of the computer where the AMDA board is attached
        '''
        ConfiguratorBase.__init__(self)
        self.host = str(host)
        self.port = int(port)
        self.client = caer_communication.caerCommunicationControlServer(host=self.host, port_control=self.port)
        self.open()

    def load_parameter_definitions(self, inp, chip):
        '''
        Parse xml file or element tree to generate the object
        '''
        if isinstance(inp, str):
            # parse the file
            doc = etree.parse(inp)
        else:
            doc = inp
        alld = dict()
        doc = doc.find('.//node[@name="{0}"]'.format(chip.id.upper()))
        for biases_root in doc.findall('.//node[@name="bias"]'):
            for br in biases_root.iterfind('.//node'):
                new_parameter = Parameter(br.attrib['name'], br.attrib['path'])
                for attr in br.iterfind('.//attr'):
                    new_parameter.add_attr(attr.attrib['key'],attr.attrib,attr.text)
                alld[new_parameter.SignalName] = new_parameter
        self.parameters = alld
    def open(self):
        '''
        Open AmdaClient
        '''
        self.client.open_communication_command()
        super(self.__class__, self).open()

    def close(self):
        '''
        Close AmdaClient
        '''
        print('closing')
        self.client.close_communication_command()
        del self.client
        super(self.__class__, self).close()

    @doc_inherit
    def set_parameter(self, param_name, param_value):
        name,key = param_name.split('.')
        path = self.parameters[name].path
        type = self.parameters[name].attr[key].data['type']
        command = 'put {path} {key} {type} {value}'.format( path = path, key = key, type=type, value = param_value)
        self.client.send_command(command)

    def set_caer_sshs(self, path, key, type, value):
        command = 'put {path} {key} {type} {value}'.format( path = path, key = key, type=type, value = value)
        self.client.send_command(command)

    def get_caer_sshs(self, path, key, type):
        command = 'get {path} {key} {type}'.format( path = path, key = key, type=type)
        return self.client.send_command(command)

    def get_param_names(self):
        #CONVENIENCE FUNCTION. IMPLEMENTATION IS NOT REQUIRED
        '''
        Returns names of all the parameters
        '''
        import numpy as np
        kv_list = []
        for name in list(self.parameters.keys()):
            for key, a in list(self.parameters[name].attr.items()):
                if key in ['coarseValue','fineValue']: kv_list.append(name+"."+key)      
        return np.sort(kv_list).tolist()


    @doc_inherit
    def get_parameter(self, param_name):
        if "." in param_name:
            name,key = param_name.split('.')
            path = self.parameters[name].path
            type = self.parameters[name].attr[key].data['type']
            command = 'get {path} {key} {type}'.format( path = path, key = key, type=type)
            value = self.client.send_command(command).strip('\x00'.encode())
            if key in ['coarseValue','fineValue']: value = int(value)
            self.parameters[name].attr[key].value = value
            return value
        else:
            name = param_name
            path = self.parameters[name].path
            kv_list = []
            for key, a in list(self.parameters[name].attr.items()):
                type = a.data['type']
                command = 'get {path} {key} {type}'.format( path = path, key = key, type=type)
                value = int(self.client.send_command(command).strip('\x00'))
                if key in ['coarseValue','fineValue']: value = int(value)
                self.parameters[name].attr[key].value = value
                kv_list.append((name+"."+key,value))
            return kv_list

        

    @doc_inherit
    def reset(self):
        pass




if __name__ == '__main__':
    c = conf_nettcpclient.Configurator(host='gillygaloo.ss.uci.edu')
    c.load_parameter_definitions('/home/eneftci/Projects/code/C/caer/caer-config.xml')
