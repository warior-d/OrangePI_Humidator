#!/usr/bin/env python
# -*- coding: utf-8 -*-

import OPi.GPIO as GPIO
from time import sleep
import sys


GPIO.setboard(GPIO.ZERO)        # Orange Pi Zero board
GPIO.setmode(GPIO.SOC)          # set up SOC numbering

S1 = GPIO.PA+20
S2 = GPIO.PA+10
KEY = GPIO.PA+9
GPIO.setup(S1, GPIO.IN)
GPIO.setup(S2, GPIO.IN)
GPIO.setup(KEY, GPIO.IN)

flag = 0
resetflag = 0
globalCount = 0

while True:
    try:
        lastSib = GPIO.input(S1)
        while not GPIO.input(KEY):
            resetflag = 1
        while not GPIO.input(S2):
            currentSib = GPIO.input(S1)
            flag =1
        
        if resetflag:
            globalCount = 0
            resetflag = 0
            print('Count reset\ncurrent = 0')
            continue
        if flag:
            if lastSib == 0 and currentSib == 1:
                print('Anticlockwise rotation')
                globalCount -= 1
            if lastSib == 1 and currentSib == 0:
                print('clockwise rotation')
                globalCount +=1
            
            flag =0
            print ('current = %s' % globalCount)
    except KeyboardInterrupt:
        print('\nExit')
        GPIO.cleanup()
        sys.exit(0)
