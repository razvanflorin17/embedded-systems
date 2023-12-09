
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


LEFT, RIGHT = INPUT_1, INPUT_4, INPUT_2, INPUT_3, OUTPUT_A, OUTPUT_D, -1, 1
TS_L, TS_R, CS, S, move_steering, LEDS, US = TouchSensor(INPUT_1), TouchSensor(INPUT_4), ColorSensor(INPUT_2), Sound(), MoveSteering(OUTPUT_A, OUTPUT_D), Leds(), UltrasonicSensor(INPUT3) 
US.mode = 'US-DIST-CM'
CONTROLLER = Controller(return_when_no_action=True)
MOTOR = Motor(move_steering)

def blue_sensor(): return read_color_sensor(CS) == "blue"
def distance_sensor(): return read_distance_sensor(ULT_S) <= 300
def black_sensor(): return read_color_sensor(CS) == "black"
def touch_sensor(): return read_touch_sensor(TOUCH_L)
def colors():
	return blue_sensor() and black_sensor()

def speaking(): S.speak("I am a robot")
def run(): MOTOR.run(rotations=10)
def beeping(): S.beep()
def go_back(): MOTOR.run(forward=False, rotations=10)
def led_red(): set_led(LEDS, "red")
def turn(): MOTOR.turn(direction=90)
def go_back_turning():
	go_back()
	turn()



class avoid_object(Behavior):
	def __init__(self):
		Behavior.__init__(self)

	def check(self):
		return distance_sensor() or touch_sensor()

	def action(self):
		go_back_turning()

