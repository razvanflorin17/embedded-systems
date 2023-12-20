#!/usr/bin/env python3

import random

from ev3dev2.motor import SpeedPercent, MoveDifferential, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.display import Display
from ev3dev2.wheel import EV3EducationSetTire
from ev3dev2.sound import Sound
from ev3dev2.led import Leds
from ev3dev2.sensor.lego import ColorSensor, TouchSensor, UltrasonicSensor
from ev3dev2._platform.ev3 import INPUT_1, INPUT_2, INPUT_3, INPUT_4
import bluetooth, threading
from commons import *
from Behaviors_master import *
if DEBUG:
    from ev3devlogging import timedlog

CS_L, CS_M, CS_R, US_B, M_L, M_R, M_A, LEFT, RIGHT = INPUT_1, INPUT_2, INPUT_3, INPUT_4, OUTPUT_A, OUTPUT_B, OUTPUT_C, -1, 1

cs_l, cs_m, cs_r, us_b, move_differential, arm_steering, leds, s = ColorSensor(CS_L), ColorSensor(CS_M), ColorSensor(CS_R), UltrasonicSensor(US_B), MoveDifferential(M_L, M_R, wheel_class=EV3EducationSetTire, wheel_distance_mm=123), MediumMotor(M_A), Leds(), Sound()

us_b.mode = 'US-DIST-CM'
motor = Motor(move_differential)
arm = ArmMotor(arm_steering)

controller = Controller(return_when_no_action=True)

my_display = Display()

master_mac = '00:17:E9:B2:1E:41'
master = True

# bluetooth_connection = BluetoothConnection(master, master_mac, debug=DEBUG)

readings_dict = {"touch_left": False, "touch_right": False, "touch_back": False, "ult_front": 1000}

# task_registry = TaskRegistry()

s.speak('Start')
if DEBUG:
    timedlog("Starting")





##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####

# controller.add(UpdateSlaveReadings(bluetooth_connection, readings_dict))
controller.add(CliffAvoidanceBhv(us_b, motor))
controller.add(EdgeAvoidanceBhv(cs_l, cs_m, cs_r, motor))
controller.add(LakeAvoidanceBhv(cs_l, cs_m, cs_r, motor, arm, measure=True))
# controller.add(RecoverCollisionBhv(readings_dict, motor))
# controller.add(AvoidCollisionBhv(readings_dict, motor))
controller.add(RunningBhv(motor, leds))


##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####


# bluetooth_connection.start_listening(lambda data: ())
controller.start()

s.speak("stop")