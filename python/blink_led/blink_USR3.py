#!/usr/bin/env python3

"""
blink_USR3.py
Author: Ismail Tambawala
Course: EDES301

Description:
    This program blinks the BeagleBone Black USR3 LED at 5 Hz 
    (i.e. 5 full on/off cycles per second).
    Uses the Adafruit_BBIO library.
-------------------------------------------------------------------------------
License:
Copyright 2025 - <Ismail Tambawala>

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, 
this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, 
this list of conditions and the following disclaimer in the documentation 
and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors 
may be used to endorse or promote products derived from this software without 
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF 
THE POSSIBILITY OF SUCH DAMAGE.
--------------------------------------------------------------------------
"""


import Adafruit_BBIO.GPIO as GPIO
import time

LED = "USR3"


GPIO.setup(LED, GPIO.OUT)

# Blink at 5 Hz → half-period = 0.1 s
try:
    while True:
        GPIO.output(LED, GPIO.HIGH)
        time.sleep(0.1)   # LED on
        GPIO.output(LED, GPIO.LOW)
        time.sleep(0.1)   # LED off
except KeyboardInterrupt:
    GPIO.output(LED, GPIO.LOW)
    GPIO.cleanup()
