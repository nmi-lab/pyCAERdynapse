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
#import cv2, PIL
#import pylab
#cv2.namedWindow('frame', cv2. WINDOW_NORMAL)

c = pyCAER.client.AEDATMonClient(host='localhost', port=7777, eventtypes=[1])

c.flush()
while True:
    events = c.fetch()
    print(events)
    raw_ad = events[:,0]
    x = (raw_ad >> 2) & 0x100
    y = (raw_ad >> 17) & 0x100
    p = (raw_ad >> 1 ) & 0x1 
    print(y,x,p)
#    ev = np.zeros([240,180], 'float')
#    ev[x,y] = 2*p-1
#    cv2.imshow('frame', PIL.Image.fromarray(np.uint8(pylab.cm.jet(ev.T*255)).convert('RGB')))
#    if cv2.waitKey(1) & 0xFF == ord('q'):
#        break
    time.sleep(.1)

