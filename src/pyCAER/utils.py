from collections import defaultdict
from contextlib import contextmanager
import numpy as np
import errno
import time
import sys
import os
from os import system
from . import globals
from getpass import getuser

class events(object):
    #Number of dimensions (address, timestamp)
    NF = 2

    def __init__(self, ev=None, atype='p', isISI=False):
        self.isISI = isISI
        assert isinstance(atype, str)
        __atype = atype[0].lower()

        if __atype == 'p':
            __dtype = np.dtype([('tm', 'uint32'),
                              ('ad', 'uint32')])

        if __atype == 'l':
            __dtype = np.dtype([('tm', 'float'),
                              ('ad', 'float')])

        self.__atype = __atype
        self.__dtype = __dtype

        if isinstance(ev, events):
            self.__data = ev.__data.copy()
        elif ev is not None:
            ev = np.array(ev)
            if ev.shape[1] == self.NF:
                self.set_data(ev[:, 0], ev[:, 1])
            elif ev.shape[0] == self.NF:
                self.set_data(ev[0, :], ev[1, :])
            else:
                raise TypeError
        else:
            self.__data = np.zeros([0], self.dtype)

    @property
    def data(self):
        return self.__data

    @property
    def atype(self):
        return self.__atype

    @property
    def dtype(self):
        return self.__dtype

    def __len__(self):
        return self.get_nev()

    def __add__(self, other):
        self.add_adtm(other.ad, other.tm)

    def __repr__(self):
        return self.get_adtm().__repr__()

    def get_nev(self):
        return len(self.get_tm())

    @property
    def nev(self):
        return self.get_nev()

    def get_tdur(self):
        if self.nev == 0:
            return 0
        if self.isISI:
            return self.tm.sum()
        else:
            if self.get_nev() > 0:
                return self.tm[-1] - self.tm[0]

    @property
    def tdur(self):
        return self.get_tdur()

    def get_t_stop(self):
        if self.isISI:
            return self.tm.sum()
        else:
            if self.get_nev() > 0:
                return self.tm[-1]

    @property
    def t_stop(self):
        return self.get_t_stop()

    def get_ad(self):
        return self.__data['ad']

    def set_ad(self, ad):
        self.__data['ad'] = ad
        return self.get_ad()

    @property
    def ad(self):
        return self.get_ad()

    #@ad.setter
    #def ad(self, value):
    #    return self.set_ad(value)

    def get_tm(self):
        return self.__data['tm']

    def set_tm(self, tm):
        self.__data['tm'] = tm
        return self.get_tm()

    @property
    def tm(self):
        return self.get_tm()

    #@tm.setter
    #def tm(self, value):
    #    return self.set_tm(value)

    def set_data(self, ad, tm):
        assert len(ad) == len(tm), "addresses and timestamps lengths are incompatible %d %d" % (len(ad), len(tm))
        self.__data = np.zeros(len(ad), self.dtype)
        self.__data['ad'] = ad.astype(self.dtype['ad'])
        self.__data['tm'] = tm.astype(self.dtype['tm'])

    def add_adtmev(self, ev):
        if not isinstance(ev, np.ndarray):
            ev = np.array(ev)

        if len(ev.shape) != self.NF:
            ev = ev.reshape(-1, 2).astype(self.dtype)

        ad = np.concatenate([self.ad, ev[:, 0]])
        tm = np.concatenate([self.tm, ev[:, 1]])
        self.set_data(ad, tm)

    def add_adtm(self, ad, tm):
        if not isinstance(ad, np.ndarray):
            ad = np.array(ad)

        if len(ad.shape) != 1:
            ad = ad.reshape(-1, 1)

        if not isinstance(tm, np.ndarray):
            tm = np.array(tm)

        if len(tm.shape) != 1:
            tm = tm.reshape(-1, 1)

        assert tm.shape == ad.shape

        ad = np.concatenate([self.ad, ad])
        tm = np.concatenate([self.tm, tm])
        self.set_data(ad, tm)

    def get_tmad(self):
        return np.array([self.tm, self.ad])

    def get_adtm(self):
        return np.array([self.ad, self.tm])

    def get_tmadev(self):
        return self.get_tmad().transpose()

    def get_adtmev(self):
        return self.get_adtm().transpose()

    def normalize_tm(self, t0=0.):
        if not self.isISI:
            t_start = self.get_tm().min()
            self.set_tm(self.get_tm() - t_start + t0)
        else:
            t = self.get_tm()
            t[0] = t0
            self.set_tm(t)

    def get_adisi(self):

        if self.isISI:
            return self.get_adtm()
        else:
            if self.nev > 0:
                tm = np.concatenate([np.array([self.tm[0]]), np.diff(self.tm)])
                return np.array([self.ad, tm])
            else:
                return np.zeros([2,0])

    def get_isiad(self):

        if self.isISI:
            return self.get_tmad()
        else:
            if self.nev > 0:
                tm = np.concatenate([np.array([self.tm[0]]), np.diff(self.tm)])
                return np.array([tm, self.ad])
            else:
                return np.zeros([2,0])

    def set_isi(self):
        if self.isISI:
            pass
        else:
            evs = self.get_adisi()
            self.set_data(evs[0],evs[1])
            self.isISI = True
            

    def set_abs_tm(self):
        '''
        Transform ISI timestamps into absolute time 
        '''
        if self.isISI:
            self.ad, self.set_tm(np.cumsum(self.get_tm()))
            self.isISI = False
        else:
            pass

    def filter_by_mapping(self, mapping):
        """
        Map the events, given a mapping dictionary like:
        map[src]=[target1,target2,...,targetn],
        """
        #The following is optimized for performance
        wasISI = False
        if self.isISI:
            wasISI = True
            self.set_abs_tm()
        evs = self.get_adtmev()
        ff = lambda x: x[0] in mapping
        filt = list(filter(ff, evs)) #keep only addresses that are mapped
        if len(filt) > 0:
            evs_filt = events(filt, self.atype).get_adtmev()
            #Get mapped addresses
            #list(chain(* concatenates lists of lists for low cost (i.e. O(n))
            m_ad = np.array(list(itertools.chain(*list(map(mapping.get, evs_filt[:, 0])))), self.dtype['ad'])
            #Get the respective timestamps
            m_tm = np.array(list(itertools.chain(*[len(mapping.get(x[0])) * [x[1]] for x in evs_filt])), self.dtype['tm'])

            self.set_data(m_ad,m_tm)
        else:
            self.empty()
        if wasISI:
            self.set_isi()

    def empty(self):
        self.__data = np.zeros([0], self.dtype)

    def iter_by_timeslice(self, tm):
        import bisect
        #ISI -> Cumulative
        if self.isISI:
            sum_tm = np.cumsum(self.get_tm())
        else:
            sum_tm = self.get_tm()
        #No in-place change
        id_start = 0
        t = 0

        #better to recycle an object rather than creating new (slow)
        evs = events(isISI=self.isISI)

        while id_start < len(sum_tm):
            t += tm
            id_stop = bisect.bisect_right(sum_tm, t, lo=id_start)
            evs.__data = self.__data[id_start:id_stop]
            id_start = id_stop
            rest = tm - evs.get_tdur()
            print((tm, evs.get_tdur()))

            if not evs.get_nev() > 0:
                rest = 0

            t -= rest
            #ISI or not is determined
            yield evs, tm - rest

    def __iter__(self):
        for ev in self.get_tmadev():
            yield ev[0],ev[1]

    def sort(self):
        '''
        Sort events by addresses and timestamps (in this order).
        '''
        self.set_abs_tm()
        self.__data.sort(order=['ad', 'tm'])

    def sort_tm(self):
        '''
        Sort events by timestamps and addresses (in this order).
        '''
        self.set_abs_tm()
        self.__data.sort(order=['tm', 'ad'])

    def demultiplex(self):
        '''
        Generates a dictionary with addesses as keys and a list of timestamps as values.
        Used internally for generating SpikeLists
        '''
        evs = events(ev=self)
        evs.sort()
        ads = np.unique(evs.ad)

        d = dict()
        k_start = 0
        k_stop = np.searchsorted(self.ad, ads, side='right')

        for i, a in enumerate(ads):
            d[a] = self.tm[k_start:k_stop[i]]
            k_start = k_stop[i]

        return d


class channelEvents(dict):
    '''
    inputs:
    *channel_events*: dictionary or channelEvents.
    *atype*: Address type 'physical' or 'logical'
    '''
    def __init__(self, channel_events=None, atype='physical'):
        assert isinstance(atype, str)
        self.__atype = atype.lower()[0]

        if isinstance(channel_events, dict):
            for k, v in list(channel_events.items()):
                self.add_ch(k, events(v, self.atype))
        elif channel_events is not None:
            raise TypeError("channel_events must be a dictionary, None or a channelEvents. Alternatively, use an events object and extract from channelAddressing")

    @property
    def atype(self):
        return self.__atype

    def copy(self):
        return channelEvents(self, atype=self.atype)

    def __add__(self, other):
        for i in list(other.keys()):
            if i in self:
                self[i] + other[i]
            else:
                self[i] = other[i]

    def __getattr__(self, attrName):
        """
        Check if the attribute exists in self, otherwise look for attributes of the encapsulated events and build a function by adding a channel argument to it.
        """
        if attrName in self.__dict__:
            return self.__dict__.__getitem__(attrName)
        else:
            def dnfun(ch, *args, **kwargs):
                return getattr(self[ch], attrName)(*args, **kwargs)
            return dnfun

    def add_ch(self, channel, ev):
        '''
        Add an events object to a channel
        Remark: Creates a reference to the provided events! In place changes also affect the events!
        '''
        assert channel not in self
        if not isinstance(ev, events):
            self[channel] = events(ev, atype=self.atype)
        else:
            self[channel] = ev

    def __len__(self):
        return self.get_nev()

    def add_adtmch(self, channel, ad, tm):
        if channel not in self:
            self[channel] = events(atype=self.atype)

        self.add_adtm(channel, ad, tm)

    def flatten(self):
        ev = events(atype=self.atype)
        for ch in self:
            ev.add_adtmev(self.get_adtmev(ch))
        return ev

    def filter_channel(self, channel_list=None):
        """
        Removes (in-place) all channels with are not in channel_list.
        If channel_list is omitted, the ch_events is left unchanged
        """
        if channel_list == None:
            return None
        all_ch = list(self.keys())
        for ch in all_ch:
            if ch not in channel_list:
                self.pop(ch)

    def get_all_tm(self):
        return self.flatten().get_tm()

    def get_last_tm(self):
        t = 0
        for evs in list(self.values()):
            t=max(t,evs.get_tm()[-1])
        return t

    def get_first_tm(self):
        t = np.inf
        for evs in list(self.values()):
            t=min(t,evs.get_tm()[0])
        return t

    def get_all_ad(self):
        return self.flatten().get_ad()

    def get_all_adtmev(self):
        return self.flatten().get_adtmev()

    def get_all_tmadev(self):
        return self.flatten().get_tmadev()

    def get_nev(self):
        n = 0
        for v in list(self.values()):
            n+=len(v)
        return n

    def iter_by_timeslice(self, tm):
        return self.flatten().iter_by_timeslice(tm)

    def filter_all_by_mapping(self, mapping):
        """
        Modifies, in-place, the encapsulated events acccording to the one-to-many mapping (key is int/float, value is iterable)
        """
        for ch in self:
            self[ch].filter_by_mapping(mapping)

    def filter_all_by_channel_mapping(self, mapping):
        """
        Modifies, in-place, the encapsulated events acccording to the one-to-many mapping (key is int/float, value is iterable)
        In this function, a different mapping is used for each channel (useful for address that do not contain channel information, for example)
        """
        for ch in self:
            self[ch].filter_by_mapping(mapping[ch])





def flatten(l):
    return [item for sublist in l for item in sublist]


def is_file_empty(filename):
    return os.stat(filename)[6] == 0


def default_user(user=None):
    if user == None:
        return getuser()
    else:
        return user


def __import_alt__(mod, alt_mod):
    '''
    import mod, if that module throws an ImportError, import alt_mod
    '''
    try:
        return __import__(mod)
    except ImportError:
        return __import__(alt_mod)


def dlist_to_dict(mapping):
    #sort list
    mapping_dict = defaultdict(list)
    func = lambda srctgt: mapping_dict[srctgt[0]].append(srctgt[1])
    list(map(func, mapping))
    return mapping_dict


@contextmanager
def empty_context():
    yield


## {{{ http://code.activestate.com/recipes/576862/ (r1)
"""
doc_inherit decorator

Usage:

class Foo(object):
    def foo(self):
        "Frobber"
        pass

class Bar(Foo):
    @doc_inherit
    def foo(self):
        pass

Now, Bar.foo.__doc__ == Bar().foo.__doc__ == Foo.foo.__doc__ == "Frobber"
"""

from functools import wraps


class DocInherit(object):
    """
    Docstring inheriting method descriptor

    The class itself is also used as a decorator
    """

    def __init__(self, mthd):
        self.mthd = mthd
        self.name = mthd.__name__

    def __get__(self, obj, cls):
        if obj:
            return self.get_with_inst(obj, cls)
        else:
            return self.get_no_inst(cls)

    def get_with_inst(self, obj, cls):

        overridden = getattr(super(cls, obj), self.name, None)

        @wraps(self.mthd, assigned=('__name__', '__module__'))
        def f(*args, **kwargs):
            return self.mthd(obj, *args, **kwargs)

        return self.use_parent_doc(f, overridden)

    def get_no_inst(self, cls):

        for parent in cls.__mro__[1:]:
            overridden = getattr(parent, self.name, None)
            if overridden:
                break

        @wraps(self.mthd, assigned=('__name__', '__module__'))
        def f(*args, **kwargs):
            return self.mthd(*args, **kwargs)

        return self.use_parent_doc(f, overridden)

    def use_parent_doc(self, func, source):
        if source is None:
            func.__doc__ = ''
        else:
            func.__doc__ = source.__doc__
        return func

doc_inherit = DocInherit
## end of http://code.activestate.com/recipes/576862/ }}}
