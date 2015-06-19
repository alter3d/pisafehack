#!/usr/bin/python -u

import RPi.GPIO as GPIO
import time

DIGIT_DELAY=0.25
CHECK_DELAY=0.2

gpioSuccessInput = 26

gpioDigitMap = [ 14, # digit 0
                 15, # digit 1
                 18, # digit 2
                 23, # digit 3
                 24, # digit 4
                 25, # digit 5
                  8, # digit 6
                  7, # digit 7
                 17, # TODO - digit 8
                 17, # TODO - digit 9 
               ]

successCombos = ""

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

def resetDigits():
    for i in range(0,10):
        GPIO.output(gpioDigitMap[i], GPIO.HIGH)
    time.sleep(DIGIT_DELAY)

def enterDigit(d):
    resetDigits()
    GPIO.output(gpioDigitMap[d], GPIO.LOW)
    time.sleep(DIGIT_DELAY)

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
    resetDigits()
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

for combo in range(0,100000):
    tryCombination(combo)

GPIO.cleanup()

