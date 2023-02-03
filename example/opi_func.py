#!/usr/bin/env python
# -*- coding: utf-8 -*-

import OPi.GPIO as GPIO
from time import sleep

GPIO.setboard(GPIO.ZEROPLUS2H3)
GPIO.setmode(GPIO.SOC)

sled = GPIO.PA+17

try:
    print(GPIO.gpio_function(sled))
    sleep(0.1)
    GPIO.setup(sled, GPIO.IN)
    sleep(0.1)
    print(GPIO.gpio_function(sled))
    sleep(0.1)
except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
   print("Keyboard interrupt")
finally:
   print("clean up")
   GPIO.cleanup()

