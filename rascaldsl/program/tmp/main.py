
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
TASK_REGISTRY = TaskRegistry()
US.mode = 'US-DIST-CM'
CONTROLLER = Controller(return_when_no_action=True)
MOTOR = Motor(move_steering)

def find_red(): return read_color_sensor(CS) == "red"
def find_blue(): return read_color_sensor(CS) == "blue"
def touch_sensor(): return read_touch_sensor(TOUCH_R) or read_touch_sensor(TOUCH_L)
def black_sensor(): return read_color_sensor(CS) == "black"
def distance_sensor(): return read_distance_sensor(ULT_S) <= 300

def go_back(): MOTOR.run(forward=False, rotations=10)
def turn(): MOTOR.turn(direction=90)
def run(): MOTOR.run(rotations=10)
def turn_run():
	run()
	turn()
def go_back_turning():
	turn()
	go_back()



class avoid_collision(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.has_fired = False
		self.suppresed = False

	def check(self):
		self.has_fired = distance_sensor()
		return self.has_fired

	def action(self):
		self.suppresed = False
		turning()
		while MOTOR.is_running and not self.supressed:
			pass
		if not self.supressed:
			return True
		else:
			timedlog("avoid_collision suppressed")
			return False

	def suppress(self):
		MOTOR.stop()
		self.supressed = True


class avoid_obstacle(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.has_fired = False
		self.suppresed = False

	def check(self):
		self.has_fired = touch_sensor()
		return self.has_fired

	def action(self):
		self.suppresed = False
		go_back_turning()
		while MOTOR.is_running and not self.supressed:
			pass
		if not self.supressed:
			return True
		else:
			timedlog("avoid_obstacle suppressed")
			return False

	def suppress(self):
		MOTOR.stop()
		self.supressed = True


class avoid_border(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.has_fired = False
		self.suppresed = False

	def check(self):
		self.has_fired = black_sensor()
		return self.has_fired

	def action(self):
		self.suppresed = False
		go_back_turning()
		while MOTOR.is_running and not self.supressed:
			pass
		if not self.supressed:
			return True
		else:
			timedlog("avoid_border suppressed")
			return False

	def suppress(self):
		MOTOR.stop()
		self.supressed = True




AAAAA

CONTROLLER.add(RunningBhv(MOTOR, LEDS, TASK_REGISTRY))

S.speak('Start')
timedlog("Starting")
CONTROLLER.start()
timedlog("Finished")

