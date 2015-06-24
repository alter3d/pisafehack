#!/usr/bin/python -u

import RPi.GPIO as GPIO
import random
import sys
import time


####################################
###  Times below are in seconds  ###
####################################

CHECKPOINT_NUM=25      # Write a checkpoint file after this many combination attempts
DIGIT_DELAY=0.10       # Delay after each digit press
CHECK_DELAY=0.25       # Delay before checking for success IN ADDITION TO DIGIT_DELAY
POWER_INTER_DELAY=0.05 # Wait time between turning power off and turning back on
POWER_POST_DELAY=0.07  # Wait time before checking next combo after power cycle


####################################################
###  NOTE: All pin numberings use BCM indexing!  ###
####################################################

gpioPowerControl = 22  # GPIO output pin that controls the relay which toggles power to the safe
gpioSuccessInput = 26  # GPIO input pin that goes high when the green LED on the safe turns on

gpioDigitMap = [ 14, # GPIO output pin that controls the relay that "presses" digit 0
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

#################################
###  Configuration ends here  ###
#################################

successCombos = ""  # A string that keeps track of valid combinations
triedCombos = {}    # A dictionary that tracks all attempted combinations


##############################
###  Initialize GPIO pins  ###
##############################

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


##########################################################
###  Cycle power to the safe's PCB with a short delay  ###
###  This short-cuts the "invalid combination" cycle   ###
###  AND the 3-invalid-attempts lockout                ###
##########################################################

def cyclePower():
    GPIO.output(gpioPowerControl, GPIO.HIGH)
    time.sleep(POWER_INTER_DELAY)
    GPIO.output(gpioPowerControl, GPIO.LOW)
    time.sleep(POWER_POST_DELAY)


#########################################################
###  Cycle power to the safe's PCB with a long delay  ###
###  This is used as part of our remedial action if   ###
###  we detect possible hardware errors               ###
#########################################################

def longCyclePower():
    print "Executing long power cycle..."
    GPIO.output(gpioPowerControl, GPIO.HIGH)
    time.sleep(5)
    GPIO.output(gpioPowerControl, GPIO.LOW)
    time.sleep(3)
    print "Done"


#######################################################
###  Reset all digits to "off"; we use this mainly  ###
###  to simulate releasing a button, but also as    ###
###  part of remedial action for hardware errors    ###
#######################################################

def resetDigits():
    for i in range(0,10):
        GPIO.output(gpioDigitMap[i], GPIO.HIGH)
    time.sleep(DIGIT_DELAY)


##########################################################################
###  Enter a digit on the keypad by activating the appropriate relay.  ###
###  We also verify that the hardware appears to be working by         ###
###  checking if the green LED goes on during the keypress.            ###
##########################################################################

def enterDigit(d):
    resetDigits()
    GPIO.output(gpioDigitMap[d], GPIO.LOW)
    time.sleep(DIGIT_DELAY)
    if GPIO.input(gpioSuccessInput) != True:
        print
        print
        print "ERROR:  The green LED did not activate from the keypress!"
        print "        Check the electrical connections to the safe's PCB."
        print
        return False
    resetDigits()
    return True


####################################################################
###  Try an entire combination by sequentially entering digits.  ###
###  Monitor for possible hardware errors and take corrective    ###
###  action if necessary.  Also check if the combo we entered    ###
###  is correct!                                                 ###
####################################################################

def tryCombination(c):
    global successCombos
    # Break the integer down into its component digits
    digits = [ c/10000,
               (c/1000)%10,
               (c/100)%10,
               (c/10)%10,
               c%10
             ]
    print "Trying combination:  ",
    for i in range(0,5):
        print "%d" % digits[i],
        # enterDigit() will return false if the digit entry failed,
        # e.g. the green light did not activate during the keypress
        # Take corrective action and try this combo again
        if enterDigit(digits[i]) != True:
            resetDigits()
            longCyclePower()
            gpioInit()
            tryCombination(c)
    time.sleep(CHECK_DELAY)
    success = GPIO.input(gpioSuccessInput)
    if success == 1:
        print "    **** FOUND A COMBO! ****",
        successCombos += "   %05d" % c
    if successCombos != "":
        print "    Valid combos are: %s" % successCombos
    else:
        print


##################################################################
###  Write current state to a file.  The state file includes   ###
###  all found combinations, if any, as well as a list of all  ###
###  attempted combinations.                                   ###
##################################################################

def saveState():
    print "Saving state to checkpoint file...",
    try:
        f = open('pisafehack.state', 'w')
        f.write(successCombos + "\n")
        for c in triedCombos.keys():
            f.write(str(c)+"\n")
        print "Wrote %d triedCombos" % len(triedCombos.keys())
        f.close()
        # Calculate an estimated time to completion for the remaining combinations
        sessionDuration = int(time.time() - sessionStartTime)
        sessionRate = int(3600 * sessionCombosTried / sessionDuration)
        timeToComplete = (100000-len(triedCombos.keys())) / sessionRate
        print "Current rate: %d combinations per hour, ETC %d hours" % ( sessionRate, timeToComplete )
    except IOError:
        print
        print "ERROR: Could not save checkpoint file!"
        sys.exit(1)


####################################################
###  Try to load a state file at startup.        ###
###  If no state file is found, just ignore the  ###
###  error and assume that this is a fresh run.  ###
###################################################

def loadState():
    global successCombos
    global triedCombos
    print "Loading state from checkpoint file..."
    try:
        f = open('pisafehack.state', 'r')
        successCombos = f.readline().rstrip()
        print "    Loaded successCombos = %s" % successCombos
        for x in f.readlines():
            triedCombos[int(x.rstrip())] = 1
        print "    Loaded %d triedCombos" % len(triedCombos.keys())
        f.close()
    except IOError:
        print "    No state file exists -- skipping!"



##################################
###  Main program entry point  ###
##################################

gpioInit()
loadState()


# Try combinations "12345" and "67890" as a hardware test.  Because we monitor
# the success of each digit press in enterDigit(), we'll see right away if
# there is a major problem with our circuit.  
print "Performing hardware test..."
tryCombination(12345)
cyclePower()
tryCombination(67890)
cyclePower()

sessionStartTime = time.time()  # Start the session timer AFTER hardware init 
sessionCombosTried = 0

print "Starting brute force..."
while True:
    c = random.randint(0,99999)
    numGen = 0
    # If our random number has already been tried, just increment
    # by 1, modulo 100000 until we find an untried one instead of 
    # generating a new random number.  We don't need true randomness.
    while triedCombos.has_key(c):
        numGen += 1
        if numGen > 110000:
            print "Tried all possible combinations -- exiting!"
            GPIO.cleanup()
            sys.exit(0)
        c += 1
        c %= 100000
    tryCombination(c)
    triedCombos[c] = 1
    sessionCombosTried += 1
    if len(triedCombos.keys()) % CHECKPOINT_NUM == 0:
        saveState()
    # Cycle power after each combination attempt to circumvent the 
    # "beep beep beep"-invalid-combination lockout.
    cyclePower()

