#!/usr/bin/env python
# ############################################################
# python class to control and save data from cAER via tcp
# author  Federico Corradi - federico.corradi@inilabs.com
# ############################################################

import os
import struct
import socket
import threading
import sys
try:
    import Queue as queue
except ImportError:
    import queue
import time
import errno
import numpy as np
from xml.dom import minidom

class caerCommunicationControlServer:
    def __init__(self, host = 'gillygaloo.ss.uci.edu',  port_control = 4040,  inputbuffersize = 8000):

        if sys.platform=="win32":
            self.USE_MSG_WAITALL = False # it doesn't work reliably on Windows even though it's defined
        else:
            self.USE_MSG_WAITALL = False#hasattr(socket, "MSG_WAITALL")

        if sys.version_info<(3, 0):
            self.EMPTY_BYTES=""
        else:
            self.EMPTY_BYTES=bytes([])

        # Note: other interesting errnos are EPERM, ENOBUFS, EMFILE
        # but it seems to me that all these signify an unrecoverable situation.
        # So I didn't include them in de list of retryable errors.
        self.ERRNO_RETRIES=[errno.EINTR, errno.EAGAIN, errno.EWOULDBLOCK, errno.EINPROGRESS]
        if hasattr(errno, "WSAEINTR"):
            self.ERRNO_RETRIES.append(errno.WSAEINTR)
        if hasattr(errno, "WSAEWOULDBLOCK"):
            self.ERRNO_RETRIES.append(errno.WSAEWOULDBLOCK)
        if hasattr(errno, "WSAEINPROGRESS"):
            self.ERRNO_RETRIES.append(errno.WSAEINPROGRESS)

        self.ERRNO_BADF=[errno.EBADF]
        if hasattr(errno, "WSAEBADF"):
            self.ERRNO_BADF.append(errno.WSAEBADF)

        self.ERRNO_ENOTSOCK=[errno.ENOTSOCK]
        if hasattr(errno, "WSAENOTSOCK"):
            self.ERRNO_ENOTSOCK.append(errno.WSAENOTSOCK)
        if not hasattr(socket, "SOL_TCP"):
            socket.SOL_TCP=socket.IPPROTO_TCP

        self.ERRNO_EADDRNOTAVAIL=[errno.EADDRNOTAVAIL]
        if hasattr(errno, "WSAEADDRNOTAVAIL"):
            self.ERRNO_EADDRNOTAVAIL.append(errno.WSAEADDRNOTAVAIL)

        self.ERRNO_EADDRINUSE=[errno.EADDRINUSE]
        if hasattr(errno, "WSAEADDRINUSE"):
            self.ERRNO_EADDRINUSE.append(errno.WSAEADDRINUSE)

        self.V2 = "aedat" # current 32bit file format
        self.V1 = "dat" # old format
        self.EVT_DVS = 0 # DVS event type
        self.EVT_APS = 1 # APS event
        self.port_control = port_control
        self.inputbuffersize = inputbuffersize
        self.host = host 
        self.s_commands = socket.socket()
        self.caer_logging = False
        self.caer_streaming = False
        self.t = None
        self.ts = None
        self.data_stream = "/tmp/data_stream.aedat"

        #caer control standards
        self.header_length = 28
        self.max_cmd_parts = 5
        self.cmd_part_action = 0
        self.cmd_part_node = 1  
        self.cmd_part_key = 2
        self.cmd_part_type = 3
        self.cmd_part_value = 4
        self.NODE_EXISTS = 0
        self.ATTR_EXISTS = 1
        self.GET = 2
        self.PUT = 3
        self.actions = { "node_exists" : [ 11, self.NODE_EXISTS ], "attr_exists" : [11, self.ATTR_EXISTS ],  "get" : [ 3, self.GET ], "put": [ 3, self.PUT ] }
        self.type_action = { 'bool':0, 'byte':1, 'short':2, \
                             'int' :3, 'long':4, 'float':5, \
                             'double':6, 'string':7 }

    def parse_command(self, command):
        '''
          parse string command
            es string: put /1/1-DAVISFX2/'+str(sensor)+'/aps/ Exposure int 10
        '''    
        databuffer = bytearray(4096)
        node_length = 0
        key_length = 0
        action_code = -1
        cmd_parts = command.split()
        if( len(cmd_parts) > self.max_cmd_parts):
            print('Error: command is made up of too many parts')
            return
        else:
            if( cmd_parts[self.cmd_part_action] != None):      # we got come action 
                action_code = self.actions[cmd_parts[0]][1]
                if(action_code == -1):
                    print("Please specify an action to perform as: get/put..")
                    return
                #do action based on action_code                 
                if(action_code == self.NODE_EXISTS):
                    node_length = len(cmd_parts[self.cmd_part_node]) + 1 
                    databuffer[0] = action_code
                    databuffer[1] = 0 #unused
                    databuffer[10:10+node_length] = self.cmd_parts[self.cmd_part_node]
                    databuffer_length = 10 + node_length
                if(action_code == self.PUT):
                    node_length  = len(cmd_parts[self.cmd_part_node]) + 1
                    key_length = len(cmd_parts[self.cmd_part_key]) + 1 
                    value_length = len(cmd_parts[self.cmd_part_value]) + 1                     
                    databuffer[0] = action_code
                    databuffer[1] = self.type_action[cmd_parts[self.cmd_part_type]]
                    databuffer[2:3] = struct.pack('H', 0)
                    databuffer[4:5] = struct.pack('H', node_length)  
                    databuffer[6:7] = struct.pack('H', key_length)
                    databuffer[8:9] = struct.pack('H', value_length)
                    databuffer[10:10+node_length] = str(cmd_parts[self.cmd_part_node]).encode('utf-8')
                    databuffer[10+node_length:10+node_length+key_length] = str(cmd_parts[self.cmd_part_key]).encode('utf-8')
                    databuffer[10+node_length+key_length:10+node_length+key_length+value_length] = str(cmd_parts[self.cmd_part_value]).encode('utf-8')
                    databuffer_length = 10 + node_length + key_length + value_length
                    #raise Exception
                if(action_code == self.GET):
                    node_length  = len(cmd_parts[self.cmd_part_node]) + 1
                    key_length = len(cmd_parts[self.cmd_part_key]) + 1 
                    value_length = 1                     
                    databuffer[0] = action_code
                    databuffer[1] = self.type_action[cmd_parts[self.cmd_part_type]]
                    databuffer[2:3] = struct.pack('H', 0)
                    databuffer[4:5] = struct.pack('H', node_length)  
                    databuffer[6:7] = struct.pack('H', key_length)
                    databuffer[8:9] = struct.pack('H', 0)
                    databuffer[10:10+node_length] = str(cmd_parts[self.cmd_part_node]).encode('utf-8')
                    databuffer[10+node_length:10+node_length+key_length] = str(cmd_parts[self.cmd_part_key]).encode('utf-8')
                    databuffer[10+node_length+key_length:10+node_length+key_length] = str('').encode('utf-8')
                    databuffer_length = 10 + node_length + key_length 
                    #raise Exception

        return databuffer[0:databuffer_length]

    def open_communication_command(self):
        '''
         open jaer UDP communication
        '''
        # create dgram udp socket
        try:
            self.s_commands = socket.socket()
            self.s_commands.connect((self.host, self.port_control))
        except socket.error as msg:
            print(('Failed to create socket %s' % msg))
            sys.exit()

    def get_header(self, data):
        '''
          get header packet
        '''
        eventtype = struct.unpack('H',data[0:2])[0]
        eventsource = struct.unpack('H',data[2:4])[0]
        eventsize = struct.unpack('I',data[4:8])[0]
        eventoffset = struct.unpack('I',data[8:12])[0]
        eventtsoverflow = struct.unpack('I',data[12:16])[0]
        eventcapacity = struct.unpack('I',data[16:20])[0]
        eventnumber = struct.unpack('I',data[20:24])[0]
        eventvalid = struct.unpack('I',data[24:28])[0]
        return [eventtype, eventsource, eventsize, eventoffset, eventtsoverflow, eventcapacity, eventnumber, eventvalid]

    def close_communication_command(self):
        '''
            close tcp communication
        '''
        try:
            self.s_commands.close()
        except socket.error as msg:
            print(('Failed to close socket %s' % msg))
            print((socket.error))
            sys.exit()


    def send_command(self, string):
        '''
            parse input command and send it to the device
            print the answer
                input string - ie. 'put /1/1-DAVISFX2/'+str(sensor)+'/aps/ Exposure int 100'
        '''    
        cmd = self.parse_command(string)    
        self.s_commands.sendall(cmd)
        msg_header = self.s_commands.recv(4)
        msg_packet = self.s_commands.recv(struct.unpack('H', msg_header[2:4])[0])
        action = struct.unpack('B',msg_header[0:1])[0]
        second = struct.unpack('B',msg_header[1:2])[0]
        print((string+' action='+str(action)+' type='+str(second)+' message='+msg_packet.decode()))
        return msg_packet

    def load_biases(self, xml_file = 'cameras/davis240c.xml', dvs128xml = False):
        '''
            load default biases as defined in the xml file
        '''
        if(dvs128xml):
            xmldoc = minidom.parse(xml_file)
            nodes = xmldoc.getElementsByTagName('node')
            value_zero = nodes[1].attributes['name'].value
            value_cam = nodes[2].attributes['name'].value 
            command = []
            #loop over xml file, get bias values and load them
            for i in range(len(nodes)):
                if(nodes[i].attributes['name'].value == 'bias' ):
                    attrs = dict(list(nodes[i].attributes.items()))
                    base_aa = 'put'
                    bias_node = nodes[i]
                    biases = bias_node.childNodes
                    for j in range(len(biases)):
                        if(biases[j].hasChildNodes()):
                            base_a = dict(list(biases[j].attributes.items()))
                            base_ab = str(attrs['path'])
                            base_b =  base_a
                            #print base_b
                            base_ac = (base_b['key'])
                            base_ad = (base_b['type'])
                            final_v = str(biases[j].firstChild.data)
                            #print final_v
                            cear_command = base_aa + " " + base_ab + " " + base_ac + " " + base_ad + " " + final_v
                            #print cear_command
                            self.send_command(cear_command)                  
        else:
            xmldoc = minidom.parse(xml_file)
            nodes = xmldoc.getElementsByTagName('node')
            value_zero = nodes[1].attributes['name'].value
            value_cam = nodes[2].attributes['name'].value 
            command = []
            #loop over xml file, get bias values and load them
            for i in range(len(nodes)):
                if(nodes[i].attributes['name'].value == 'bias' ):
                    attrs = dict(list(nodes[i].attributes.items()))
                    base_aa = 'put'
                    bias_node = nodes[i]
                    biases = bias_node.childNodes
                    for j in range(len(biases)):
                        if(biases[j].hasChildNodes()):
                            base_a = dict(list(biases[j].attributes.items()))
                            #print base_a
                            base_ab = (base_a['path'])
                            if(biases[j].hasChildNodes()):
                                bias_values = biases[j].childNodes
                                for k in range(len(bias_values)):
                                    if(bias_values[k].hasChildNodes()):
                                        base_b = dict(list(bias_values[k].attributes.items())) 
                                        #print base_b
                                        base_ac = (base_b['key'])
                                        base_ad = (base_b['type'])
                                        final_v = str(bias_values[k].firstChild.data)
                                        #print final_v
                                        cear_command = base_aa + " " + base_ab + " " + base_ac + " " + base_ad + " " + final_v
                                        #print cear_command
                                        self.send_command(cear_command)                  

if __name__ == '__main__':
    c = caerCommunicationControlServer()
