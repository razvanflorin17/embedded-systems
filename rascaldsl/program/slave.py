#!/usr/bin/env python3

import random

from ev3dev2.motor import SpeedPercent, MoveSteering, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.display import Display
from ev3dev2.sound import Sound
from ev3dev2.led import Leds
from ev3dev2.sensor.lego import ColorSensor, TouchSensor, UltrasonicSensor
from ev3dev2._platform.ev3 import INPUT_1, INPUT_2, INPUT_3, INPUT_4
import bluetooth, threading

from commons import *
from Behaviors_slave import *
if DEBUG:
    from ev3devlogging import timedlog

TS_L, TS_R, TS_B, US_F, LEFT, RIGHT = INPUT_1, INPUT_2, INPUT_3, INPUT_4, -1, 1

ts_l, ts_r, ts_b, us_f, s = TouchSensor(TS_L), TouchSensor(TS_R), TouchSensor(TS_B), UltrasonicSensor(US_F), Sound()
us_f.mode = 'US-DIST-CM'

controller = Controller(return_when_no_action=True)

master_mac = '78:DB:2F:2B:5D:98'
master = False

bluetooth_connection = BluetoothConnection(master, master_mac, debug=DEBUG)
readings_dict = {"touch_left": False, "touch_right": False, "touch_back": False, "ult_front": 0}


controller.add(UpdateSlaveReadingsBhv(ts_l, ts_r, ts_b, us_f, bluetooth_connection, readings_dict))



s.speak('Start')
if DEBUG:
    timedlog("Starting")





##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####





##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####





bluetooth_connection.start_listening(lambda data: ())
controller.start()

s.speak("stop")