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

from commons import *
from Behaviors_slave import *

TS_L, TS_R, TS_B, US_F, LEFT, RIGHT = INPUT_1, INPUT_2, INPUT_3, INPUT_4, -1, 1

ts_l, ts_r, ts_b, us_f, s = TouchSensor(TS_L), TouchSensor(TS_R), TouchSensor(TS_B), UltrasonicSensor(US_F), Sound()

controller = Controller(return_when_no_action=True)

master_mac = '00:17:E9:B2:6C:86'
master = False

bluetooth_connection = BluetoothConnection(master, master_mac, debug=True)
readings_dict = {"touch_left": False, "touch_right": False, "touch_back": False, "ult_front": 0}


controller.add(UpdateSlaveReadings(ts_l, ts_r, ts_b, us_f, bluetooth_connection, readings_dict))



s.speak('Start')
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