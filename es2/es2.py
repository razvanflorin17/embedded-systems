#!/usr/bin/env python3

from ev3dev2.display import Display
from ev3dev2.sensor.lego import ColorSensor, TouchSensor, UltrasonicSensor
from ev3dev2._platform.ev3 import INPUT_2, INPUT_4, INPUT_1, INPUT_3
from ev3dev2.sound import Sound
from ev3dev2.motor import MoveSteering, OUTPUT_A, OUTPUT_D, OUTPUT_C, MediumMotor
from ev3dev2.led import Leds
from ev3devlogging import timedlog
from Subs_arch import Controller
from commons import *
from Behaviors import *


# TS_L, TS_R, CS, US, M_L, M_R, LEFT, RIGHT = INPUT_1, INPUT_4, INPUT_2, INPUT_3, OUTPUT_A, OUTPUT_D, -1, 1
# master_mac = '78:DB:2F:29:F0:39'
# master = False

# my_display = Display()
# ts_l, ts_r, cs, s, move_steering, leds, us = TouchSensor(TS_L), TouchSensor(TS_R), ColorSensor(CS), Sound(), MoveSteering(M_L, M_R), Leds(), UltrasonicSensor(INPUT_3) 
# controller = Controller(return_when_no_action=True)
# motor = Motor(move_steering)

# bluetooth_connection = BluetoothConnection(master, master_mac, debug=True)

# task_registry = TaskRegistry()
# task_registry.add("color_task")
# color_dict = {"red": False, "yellow": False, "blue": False}

# controller.add(ColorSensorBhv(cs, motor, leds, s))
# controller.add(ReceiveDetectedColorBhv(color_dict, bluetooth_connection, leds, s))
# controller.add(DetectColorBhv(cs, color_dict, bluetooth_connection, leds, s))
# controller.add(TouchSensorsBhv(ts_l, ts_r, motor, leds, s))
# controller.add(UltrasonicSensorBhv(us, motor, leds, s))
# controller.add(UpdateColorTaskBhv(color_dict, task_registry, "color_task", leds, s))
# controller.add(RunningBhv(motor, leds, task_registry))

s=Sound()

s.speak('Start')
timedlog("Starting")

motor = ArmMotor(MediumMotor(OUTPUT_C))
motor.move(up=False, rotations=0.25, block=False) 

# bluetooth_connection.start_listening(lambda data: ())
# controller.start()

# s.speak("stop")