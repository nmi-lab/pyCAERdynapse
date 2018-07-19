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
import cv2

c = pyCAER.client.AEDATMonClient(host='localhost', port=7777, eventtypes=[1])

cv2.namedWindow('frame', cv2. WINDOW_NORMAL)

while True:
    events = c.fetch()
    raw_ad = events.get_ad()
    x = (raw_ad >> 12) & (2**10-1)

    time.sleep(.1)

