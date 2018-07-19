#!/bin/python
#-----------------------------------------------------------------------------
# File Name : run_davis240.py
# Author: Emre Neftci
#
# Creation Date : Thu 19 Jul 2018 10:31:57 AM MDT
# Last Modified : 
#
# Copyright : (c) UC Regents, Emre Neftci
# Licence : GPLv2
#----------------------------------------------------------------------------- 
import pyCAER
import time
#import cv2
#cv2.namedWindow('frame', cv2. WINDOW_NORMAL)

c = pyCAER.client.AEDATMonClient(host='localhost', port=7777, eventtypes=[1])

c.flush()
while True:
    events = c.fetch()
    raw_ad = events[:,0]
    x = (raw_ad >> 12) & 0x3ff
    y = (raw_ad >> 22) & 0x3ff
    p = (raw_ad >> 62) 
    print(x,y,p)
    #ev = np.zeros([240,180], 'float')
    time.sleep(.1)

