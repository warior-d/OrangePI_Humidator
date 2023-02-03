#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import OPi.GPIO as GPIO
from time import sleep          # this lets us have a time delay
import Encoder

#GPIO.setboard(GPIO.PCPCPLUS)    # Orange Pi PC board

GPIO.setboard(GPIO.LITE)    # Orange Pi PC board
#GPIO.setmode(GPIO.BOARD)        # set up BOARD BCM numbering
GPIO.setmode(GPIO.SOC)
cont = GPIO.PA+6
GPIO.setup(cont, GPIO.OUT)         # set BCM7 (pin 26) as an output (LED)
#GPIO.setup(19, GPIO.IN)
#GPIO.setup(22, GPIO.IN)

#enc = Encoder.Encoder(10, 20)

try:
    print ("Press CTRL+C to exit")
    while True:
        GPIO.output(cont, 1)       # set port/pin value to 1/HIGH/True
        sleep(1.1)
        GPIO.output(cont, 0)       # set port/pin value to 0/LOW/False
        sleep(1.1)

        GPIO.output(cont, 1)       # set port/pin value to 1/HIGH/True
        sleep(1.1)
        GPIO.output(cont, 0)       # set port/pin value to 0/LOW/False
        sleep(1.1)
#        print(enc.read())
        sleep(1.5)

except KeyboardInterrupt:
    GPIO.output(cont, 0)           # set port/pin value to 0/LOW/False
    GPIO.cleanup()              # Clean GPIO
    print ("Bye.")
