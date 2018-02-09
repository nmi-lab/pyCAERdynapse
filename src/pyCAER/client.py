import threading
import socket, struct
try:
    import Queue as queue
except ImportError:
    import queue
#For probing network buffer
import fcntl
from termios import FIONREAD
from contextlib import contextmanager
#AER related
import pyNCSre.pyST as pyST
from .utils import *

#Special events used to control reset and synchonization
GOEVENT = np.array([-1, 0], dtype='uint32').tostring() #for stim = None, this ensures that the hold is released.
HOLDEVENT = np.array([-2, 0], dtype='uint32').tostring() #Hold and reset: the aex device file is opened immediately before the next event is receied

VALID_SHIFT = 0
VALID_WIDTH = 1
VALID_MASK = 2**VALID_WIDTH-1
CHIP_SHIFT = 6
CHIP_WIDTH = 4
CHIP_MASK = 2**CHIP_WIDTH-1
CHIP_NMASK = 2**32-1 - ((2**CHIP_WIDTH-1)<<CHIP_SHIFT)


class AEDATClientBase(threading.Thread):
    '''
    This class starts a Monitor client for the AEDAT server. Once created, this continously reads the monitored events.
    '''
    #Singleton: make sure a client is only instantiated once in a session
    def __init__(self,
            host='gillygaloo.ss.uci.edu',
            port=7778,
            autostart=True,
            qsize=4096,
            ):
        '''
        *MonChannelAddress:* Monitor Channel Addressing object, if omitted, default channel is taken
        *host:* Monitoring AEDAT server hostname.
        *port:* Port of the Monitoring Server (Default 50001)
        *qsize:* The maxsize of the queue
        '''
        threading.Thread.__init__(self)
        self.daemon = True  # The entire Python program exits when no alive non-daemon threads are left
        print(("Connecting to " + host))
        #self.aexfd = os.open("/dev/aerfx2_0", os.O_RDWR | os.O_NONBLOCK)
        self.finished = threading.Event()
        self.buffer = queue.Queue(qsize)  # 8192 packets in Queue=~5min

        self.MonChannelAddress = pyST.getDefaultMonChannelAddress()


        self.recvlock = threading.Lock()
        self._nbufferempty = False
        self.eventsPacket = np.array([])
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port_mon = int(port)

        self.sock.connect((self.host, self.port_mon))

        self.data_header = self.sock.recv(20)
        # Set the socket to non-blocking (with timeout) to avoid the thread
        # being stuck. Because of this, I must catch EWOULDBLOCK error
        #Frame period
        self.fT = 1./50
        self.sock.settimeout(5.0)


        #Build decoder functions
        if autostart:
            self.start()

    def run(self):
        while self.finished.isSet() != True:
            t0 = time.time()

            with self.recvlock:
                self.fetch_raw()

            #Fastest frame rate should be 1/fT. Wait in case we've been faster
            t_left = self.fT - (time.time() - t0)
            if t_left > 0:
                time.sleep(t_left)
            # Ok now check how much data is available and choose a multiple of
            # 8 (AE packet size

    def flush(self, verbose=False):
        '''
        empties the buffers.
        '''

        #empty Queue buffer
        with self.recvlock:
            self.buffer.queue.clear()
#           while True:
#               try:
#                   self.buffer.get(False)
#               except queue.Empty:
#                   break

    def stop(self):
        self.finished.set()
        with self.recvlock:
            self.sock.close()

    def __del__(self):
        self.stop()


##################
##Mapper functions
class AEDATMonClient(AEDATClientBase):

    def _recv_packet(self):
        data_ev_head = self.sock.recv(28)  # we read the header of the packet
        while len(data_ev_head)<28:
            data_ev_head += self.sock.recv(28-len(data_ev_head))
            print('reread')


        
        # read header
        eventtype = struct.unpack('H', data_ev_head[0:2])[0]
        eventsource = struct.unpack('H', data_ev_head[2:4])[0]
        eventsize = struct.unpack('I', data_ev_head[4:8])[0]
        eventoffset = struct.unpack('I', data_ev_head[8:12])[0]
        eventtsoverflow = struct.unpack('I', data_ev_head[12:16])[0]
        eventcapacity = struct.unpack('I', data_ev_head[16:20])[0]
        eventnumber = struct.unpack('I', data_ev_head[20:24])[0]
        eventvalid = struct.unpack('I', data_ev_head[24:28])[0]
        next_read = eventcapacity * eventsize
        if(eventtype == 12):
            data = ''.encode()
            while len(data)<next_read:
                data += self.sock.recv(next_read-len(data))
            return data, eventvalid
        else:
            return '', 0

    def put_buffer(self, ev):
        try:
            self.buffer.put(ev, block=False)
        #Drop last and put new
        except queue.Full:
            self.buffer.get(block=True)
            self.buffer.put(ev, block=True)

    @contextmanager
    def _isbuffernotempty(self, ev, nev):
        try:
            yield
            self._nbufferempty = True
        except ValueError:
            if not ev == '' and nev == -1:
                self._nbufferempty = True  # queue is not empty
                pass
            else:
                self._nbufferrempty = False  # queue is not empty
                pass

    def _extract_events(self, ev):
        if ev == '':
            raise ValueError()

        tmp_array = np.fromstring(ev, dtype='uint32')

        #Do swap if big endian system
        if sys.byteorder == 'big':
            tmp_array.byteswap(True)
        evs = events(tmp_array.reshape(-1, 2), atype='p')

        return evs

    def fetch_raw(self):
        '''
        This functions is called by threading.Thread.run to read from the TCP fifo and add an event packet (a STas.events object) to the client's buffer in physical format.
        '''
        eventsPacket, nev = self._recv_packet()
        
        with self._isbuffernotempty(eventsPacket, nev):
            #Read from binary
            evs = self._extract_events(eventsPacket)
            #extract logical for all channels
            self.put_buffer(evs)

        return self._nbufferempty

    def fetch(self):
        '''
        Empties the buffer and returns its contents
        returns numpy.array in raw address - timestamp format.
        '''
        x = events(atype='p')
        while True:
            try:
                x.add_adtmev(self.buffer.get(block=False).get_adtmev())
            except queue.Empty:
                return x.get_adtmev()

    def listen(self, tDuration=1000, filter_duplicates=False):
        '''
        empties the queue & returns a SpikeList containing the data that was in the Queue
        synposis: client.flush(); time.sleep(1); out=client.listen()
        @author emre@ini.phys.ethz.ch, andstein@student.ethz.ch

        *tDuration*: is a float defining the duration to be listened (in ms)
        *output*: is a string defining in what form the output should be returned. Default is SpikeList where a NeuroTools.signal SpikeList is returned. Other possiblities are 'array' where a normalized numpy array is returned and 'raw' where a pyST.channelEvents object is returned.
        *filter_duplicates* if True erase in all channels double events within the a 0.01ms time-frame (buggy hw)
        '''

        #initialize output channelEvents
        out = events(atype='p')
        target_delta = tDuration*1000
        data_delta = 0
        while data_delta < target_delta:
            try:
                evs = self.buffer.get(block=True)
            except queue.Empty:
                continue

            if evs.get_nev() > 0:
                ad = evs.get_ad()
                tm = evs.get_tm()
                valid = (ad&VALID_MASK).astype('bool')
                chip = (ad[valid]>>CHIP_SHIFT)&CHIP_MASK
                ad[valid] = ad[valid]&CHIP_NMASK
                ad = ad[valid]>>VALID_WIDTH
                tm = tm[valid]
                ad += chip<<28
                out.add_adtm(ad,tm)
            #Assumes isi
            data_delta = (out.get_tm()[-1] - out.get_tm()[0])
                    
        tm = out.get_tm()
        tm = tm - tm[0]
        out.set_tm(tm)
        return out.get_adtmev()


class AEDATClient(AEDATMonClient):
    '''
    This class starts a Monitor/Stimulation client for the AEDAT server. Once started, this continously reads the monitored events.
    '''
    def __init__(self,
            host='gillygaloo.ss.uci.edu',
            host_stim=None,
            port_mon=7778,
            port_stim=50002,
            autostart=True,
            qsize=4096,
            ):
        '''
        *MonChannelAddress:* Monitor Channel Addressing object, if omitted, default channel is taken
        *SeqChannelAddress:* Sequencer Channel Addressing object, if omitted, default channel is taken
        *host:* Monitoring and Sequencing AEDAT server hostname. (Must be same)
        *port_mon:* Port of the Monitoring Server (Default 50001)
        *port_stim:* Port of the Monitoring Server (Default 50002)
        *qsize*: is the size of the queue (FIFO). This is automatically adjusted if the buffer is too small.
        '''

        self.MonChannelAddress = pyST.getDefaultMonChannelAddress()
        self.SeqChannelAddress = pyST.getDefaultSeqChannelAddress()

        AEDATMonClient.__init__(
                self, 
                host=host,
                port=port_mon,
                autostart=False,
                qsize=qsize,
                )

        if host_stim == None:
            self.host_stim = host
        else:
            self.host_stim = host_stim

        #self.aexfd = os.open("/dev/aerfx2_0", os.O_RDWR | os.O_NONBLOCK)
        #self.stim_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.stim_sock.connect((self.host_stim, int(port_stim)))

        if autostart:
            self.start()

    def stimulate(self,
            stim=None,
            tDuration=None,
            context=None,
            filter_duplicates=False,
            debug=False,
            verbose=True,
            ):
        '''
        NOTE: OLD DOCUMENTATION !!
        This function stimulates through AEDAT server. **NOT** network lag invariant!
        *stim:* should be a SpikeList (usable by channelAddressing.exportAER())
        *tDuration:* in ms (Default: guess from stim or 1000 if stim==None).
        *isi:* Whether the input should be send to server as inter-spike intervals.
        *send_reset_event* resets the AEDAT board when stimulated (experimental).
        *output* format of output, spikelist/array/raw/
        *context* is a context which is executed before and after the stimulation (for sync functions and clean-up functions for example, see the python contextlib module).
        *filter_duplicates* if True erase in all channels double events within the a 0.01ms time-frame (buggy hw)
        '''

        if context == None:
            context = empty_context

        stim = events(None, 'p') #stimulus disabled!

        if sys.byteorder == 'big':
            stimByteStream = stim.get_tmadev().byteswap().tostring()
        else:
            stimByteStream = stim.get_tmadev().tostring()

        if verbose:
            print("Bytecoding input...")
            #print((np.fromstring(stimByteStream, 'uint32')))
            print("Done")

        if tDuration == None:
            tDuration = np.sum(stim.get_tm()) * 1e-3  # from us to ms

        if self.buffer.maxsize / self.fT < tDuration:
            while self.buffer.maxsize / self.fT < tDuration:
                self.buffer.maxsize *= 2

        #Clean up pre-stimulus data
        if verbose:
            print("Flushing pre-stimulus data...")
        self.flush()

        if verbose:
            print(("Sending to " + self.host))

        if len(stim)>0:
            if verbose:
                print((np.fromstring(stimByteStream, 'uint32')))

            if send_reset_event:
                self.stim_sock.send(HOLDEVENT)
                self.flush()  # Be sure that there are no events left in the buffer
                # Since the monitor is held, no events can come in until the
                # reset. Well... in theory
                #Bug: Somehow, a few event still get through...
            with context():
                #self.buffer.put(-1, block=True)
                self.stim_sock.send(stimByteStream)
                time.sleep(tDuration * 1e-3 + tDuration * 1.0 * 1e-3 + .100)

        else:
            if verbose:
                print(("Waiting " + str(
                    tDuration) + "ms " + "for stimulation to finish"))

        #####
        # Throw away pre-stimulus data
        #if verbose:
        #    print "Throwing away pre-stimulus-data"

        #while self.buffer.get() != -1:
        #    pass

        if verbose:
            print("Recieving...")
        received = self.listen(tDuration=tDuration, filter_duplicates=filter_duplicates)
        return received
            
    def stop(self):
        self.finished.set()
        with self.recvlock:  # Be sure that there is no fetching going on
            self.sock.close()
        #with self.stimlock # there is no stimlock
        #self.stim_sock.close()

    def __del__(self):
        self.stop()

            
if __name__ == '__main__':
    c = AEDATMonClient()


