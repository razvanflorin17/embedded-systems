
    rVal += "#!/usr/bin/env python3

import random

from ev3dev2.motor import SpeedPercent, MoveSteering, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.display import Display
from ev3dev2.sound import Sound
from ev3dev2.led import Leds
from ev3dev2.sensor.lego import ColorSensor, TouchSensor, UltrasonicSensor
from ev3dev2._platform.ev3 import INPUT_1, INPUT_2, INPUT_3, INPUT_4
import bluetooth, threading

if DEBUG:
    from ev3devlogging import timedlog

TS_L, TS_R, TS_B, US_F, LEFT, RIGHT = INPUT_1, INPUT_2, INPUT_3, INPUT_4, -1, 1

TS_L, TS_R, TS_B, US_F, S = TouchSensor(TS_L), TouchSensor(TS_R), TouchSensor(TS_B), UltrasonicSensor(US_F), Sound()
US_F.mode = \'US-DIST-CM\'


BLUETOOTH_CONNECTION = BluetoothConnection(MASTER, MASTER_MAC, debug=DEBUG)
READINGS_DICT = {\"TS_L\": False, \"TS_R\": False, \"TS_B\": False, \"US_F\": 0}



#!/usr/bin/env python3

import random

from ev3dev2.motor import SpeedPercent, MoveSteering, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.display import Display
from ev3dev2.sound import Sound
from ev3dev2.led import Leds
from ev3dev2.sensor.lego import ColorSensor, TouchSensor, UltrasonicSensor
from ev3dev2._platform.ev3 import INPUT_1, INPUT_2, INPUT_3, INPUT_4
from ev3devlogging import timedlog

import bluetooth, threading
import time

from Subs_arch import Behavior, Controller
from commons import *



class UpdateSlaveReadingsBhv(Behavior):
    \"\"\"
    This behavior will check if the robot touch an object, and tries to step away from it
    \"\"\"
    
    def __init__(self):
        \"\"\"
        Initialize the behavior
        @param touch_left: The left touch sensor to use
        @param touch_right: The right touch sensor to use
        @param touch_back: The back touch sensor to use
        @param ult_front: The front ultrasonic sensor to use
        @param bluetooth_connection: The bluetooth connection to use
        @param readings_dict: The readings dictionary to update and send
        
        \"\"\"
        Behavior.__init__(self)

        self.direction = None

    
    def check(self):
        \"\"\"
        Check if the touch sensor is pressed
        @return: True if the touch sensor is pressed
        @rtype: bool
        \"\"\"
        return True
        

    def action(self):
        \"\"\"
        Update the dictionary with the new readings and send them to the master
        \"\"\"

        READINGS_DICT[\"TS_L\"] = read_touch_sensor(TL)
        READINGS_DICT[\"TS_R\"] = read_touch_sensor(TR)
        READINGS_DICT[\"TS_B\"] = read_touch_sensor(TB)
        READINGS_DICT[\"US_F\"] = read_ultrasonic_sensor(US_F)

        msg = str(READINGS_DICT[\'TS_L\']) + \",\" + str(READINGS_DICT[\'TS_R\']) + \",\" + str(READINGS_DICT[\'TS_B\']) + \",\" + str(READINGS_DICT[\'US_F\'])
        log = \"Sending Readings: \" + msg
        if DEBUG:
            timedlog(log)
        BLUETOOTH_CONNECTION.write(msg)
        
        time.sleep(0.05)

        return True


    def suppress(self):
        \"\"\"
        Suppress the behavior
        \"\"\"
        pass

            '";