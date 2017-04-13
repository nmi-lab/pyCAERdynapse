from pyNCS.api.ConfAPI import MappingsBase
from pyAex.aexutils import doc_inherit, getuser, get_MAPHOST, get_MAPVERS
from pyAex.aexutils import set_MAPHOST, set_MAPVERS
#Load DongChen's ConnectNeurons class in connect_neurons.py here (replace next line)
import pyAex.mapclient as mapclient

class Mappings(MappingsBase):
    @doc_inherit
    def __init__(self, debug=False, *args, **kwargs):
        self.debug = debug
        super(self.__class__, self).__init__()

    @doc_inherit
    def add_mappings(self, mappings):

        mapclient.setMappings(mappings)
        if self.debug:
            print "Successfully written {0} connections".format(len(mappings))

    @doc_inherit
    def get_mappings(self):
        cur_table = mapclient.getMapping()
        if self.vers < 3:
            cur_table = cur_table.reshape(-1, 2)
        elif self.vers == 3:
            cur_table = cur_table.reshape(-1, 3)
        return cur_table

    @doc_inherit
    def clear_mappings(self):
        mapclient.clearAllMappings()
        return None
