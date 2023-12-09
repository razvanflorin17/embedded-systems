#!/usr/bin/env python3

from ev3dev2.display import Display
from ev3dev2.sensor.lego import ColorSensor, TouchSensor, UltrasonicSensor
from ev3dev2._platform.ev3 import INPUT_2, INPUT_4, INPUT_1, INPUT_3
from ev3dev2.sound import Sound
from ev3dev2.motor import MoveSteering, OUTPUT_A, OUTPUT_D
from ev3dev2.led import Leds
from ev3devlogging import timedlog
from Subs_arch import Controller, Behavior
from commons import *
from Behaviors import *


TS_L, TS_R, CS, US, M_L, M_R, LEFT, RIGHT = INPUT_1, INPUT_4, INPUT_2, INPUT_3, OUTPUT_A, OUTPUT_D, -1, 1

my_display = Display()
ts_l, ts_r, cs, s, move_steering, leds, us = TouchSensor(TS_L), TouchSensor(TS_R), ColorSensor(CS), Sound(), MoveSteering(M_L, M_R), Leds(), UltrasonicSensor(INPUT_3) 
controller = Controller(return_when_no_action=True)
motor = Motor(move_steering)


task_registry = TaskRegistry()
task_registry.add("color_task")
color_dict = {"red": False, "yellow": False, "blue": False}

controller.add()

s.speak('Start')
timedlog("Starting")


bluetooth_connection.start_listening(lambda data: ())
controller.start()

s.speak('Stop')

