#!/usr/bin/env python
# -*- coding: utf-8 -*-

import OPi.GPIO as GPIO
from time import sleep
import sys

GPIO.setboard(GPIO.ZERO)  # Orange Pi Zero board
GPIO.setmode(GPIO.SOC)  # set up SOC numbering

S1 = GPIO.PA+20
S2 = GPIO.PA+10
KEY = GPIO.PA+8

GPIO.setup(S1, GPIO.IN)
GPIO.setup(S2, GPIO.IN)
#GPIO.setup(KEY, GPIO.IN)
GPIO.setup(KEY, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

flag = 0
resetflag = 0
globalCount = 0


try:
    while True:

        GPIO.add_event_detect(KEY, GPIO.BOTH)

        if GPIO.event_detected(KEY):
            print('Button pressed')

except KeyboardInterrupt:
    print("Exit pressed Ctrl+C")

finally:
    GPIO.cleanup()
    print("End of program")
