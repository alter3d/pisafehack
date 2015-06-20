#!/usr/bin/python -u

import RPi.GPIO as GPIO
import random
import sys
import time

DIGIT_DELAY=0.25  # Delay after each digit press
CHECK_DELAY=0.00  # Additional delay before checking for success IN ADDITION to DIGIT_DELAY
POWER_INTER_DELAY=0.05 # Wait time between turning power off and turning back on
POWER_POST_DELAY=0.05  # Wait time before checking next combo after power cycle

gpioPowerControl = 22
gpioSuccessInput = 5

gpioDigitMap = [ 14, # digit 0
                 15, # digit 1
                 18, # digit 2
                 23, # digit 3
                 24, # digit 4
                 25, # digit 5
                  8, # digit 6
                  7, # digit 7
                 17, # digit 8
                 27, # digit 9 
               ]

successCombos = ""
triedCombos = {}

def gpioInit():
    print "Initializing GPIO..."
    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    for i in range(0,10):
        print "    Setting BCM # %d as output for digit %d..." % (gpioDigitMap[i], i)
        GPIO.setup(gpioDigitMap[i], GPIO.OUT, initial=1)
    print "    Setting BCM # %d as success input..." % gpioSuccessInput
    GPIO.setup(gpioSuccessInput, GPIO.IN)
    print "    Setting BCM # %d as power control..." % gpioPowerControl
    GPIO.setup(gpioPowerControl, GPIO.OUT, initial=0)
    cyclePower()

def cyclePower():
    print "Cycling power... off...",
    GPIO.output(gpioPowerControl, GPIO.HIGH)
    time.sleep(POWER_INTER_DELAY)
    print "on...",
    GPIO.output(gpioPowerControl, GPIO.LOW)
    print "wait...",
    time.sleep(POWER_POST_DELAY)
    print "done"

def resetDigits():
    for i in range(0,10):
        GPIO.output(gpioDigitMap[i], GPIO.HIGH)
    time.sleep(DIGIT_DELAY)

def enterDigit(d):
    resetDigits()
    GPIO.output(gpioDigitMap[d], GPIO.LOW)
    if GPIO.input(gpioSuccessInput != 1:
        print
        print
        print "ERROR:  The green LED did not activate from the keypress!"
        print "        Check the electrical connections to the safe's PCB."
        print
        sys.exit(1)
    time.sleep(DIGIT_DELAY)
    resetDigits()

def tryCombination(c):
    global successCombos
    digits = [ c/10000,
               (c/1000)%10,
               (c/100)%10,
               (c/10)%10,
               c%10
             ]
    print "Trying combination:  ",
    for i in range(0,5):
        print "%d" % digits[i],
        enterDigit(digits[i])
    time.sleep(CHECK_DELAY)
    success = GPIO.input(gpioSuccessInput)
    if success == 1:
        print "    **** FOUND A COMBO! ****",
        successCombos += "   %05d" % c
    if successCombos != "":
        print "    Valid combos are: %s" % successCombos
    else:
        print

gpioInit()

while True:
    c = random.randint(0,99999)
    numGen = 0
    while triedCombos.has_key(c):
        numGen += 1
        if numGen > 200000:
            print "Tried all possible combinations -- exiting!"
            GPIO.cleanup()
            sys.exit(0)
        c += 1
        c %= 100000
    tryCombination(c)
    triedCombos[c] = 1
    cyclePower()

GPIO.cleanup()

