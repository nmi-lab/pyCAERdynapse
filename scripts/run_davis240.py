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
import numpy as np
import cv2, PIL
import pylab
cv2.namedWindow('frame', cv2. WINDOW_NORMAL)

c = pyCAER.client.AEDATMonClient(host='localhost', port=7777, eventtypes=[1])

c.flush()
while True:
    events = c.listen_raw()
    print(len(events))
    raw_ad = events[:,0]
    x = (raw_ad >> 2) & 0xff
    y = (raw_ad >> 17) & 0xff
    p = (raw_ad >> 1 ) & 0x1 
    #print(x,y,p)
    ev = np.zeros([240,180], 'float')
    ev[y,x] = 2*p-1
    cv2.imshow('frame', ev)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    time.sleep(.01)

