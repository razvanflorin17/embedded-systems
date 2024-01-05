

"211"

[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(592,2,<29,80>,<29,82>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(597,2,<29,85>,<29,87>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(602,2,<29,90>,<29,92>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(587,2,<29,75>,<29,77>)]


class bb_bhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.suppresed = False
		self.operations = []
		self.has_fired = False


	def _reset(self):
		self.operations = []
		MOTOR.stop()
		if not self.suppresed:
			self.has_fired = False


	def check(self):
		fire_cond = (read_color_sensor(CS_M) == "black" and readings_dict[TOUCH_L] and read_color_sensor(CS_L) == "black" and read_ultrasonic_sensor(ULT_B) < 10)
		if fire_cond != self.has_fired:
			self.has_fired = fire_cond
			if self.has_fired:
				self.operations = [lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: S.beep()]
				return True

		return False


	def action(self):
		self.suppresed = False
		if DEBUG:
			timedlog("bb fired")

		for operation in self.operations:
			operation()
			while MOTOR.is_running and not self.supressed:
				pass
			if self.supressed:
				break

		self._reset()

		if DEBUG and not self.supressed:
			timedlog("bb done")
		return not self.supressed


	def suppress(self):
		MOTOR.stop()
		self.supressed = True
		if DEBUG:
			timedlog("bb suppressed")




class bc_bhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.suppresed = False
		self.operations = []
		self.has_fired = False


	def _reset(self):
		self.operations = []
		MOTOR.stop()
		if not self.suppresed:
			self.has_fired = False


	def check(self):
		fire_cond = (read_color_sensor(CS_M) == "black" or read_color_sensor(CS_L) == "black" or read_ultrasonic_sensor(ULT_B) < 10)
		if fire_cond != self.has_fired:
			self.has_fired = fire_cond
			if self.has_fired:
				self.operations = [lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: S.beep(), lambda: MOTOR.turn(direction="RIGHT", degrees=90, speed=30)]
				return True

		return False


	def action(self):
		self.suppresed = False
		if DEBUG:
			timedlog("bc fired")

		for operation in self.operations:
			operation()
			while MOTOR.is_running and not self.supressed:
				pass
			if self.supressed:
				break

		self._reset()

		if DEBUG and not self.supressed:
			timedlog("bc done")
		return not self.supressed


	def suppress(self):
		MOTOR.stop()
		self.supressed = True
		if DEBUG:
			timedlog("bc suppressed")




class bd_bhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.suppresed = False
		self.operations = []
		self.has_fired = False


	def _reset(self):
		self.operations = []
		MOTOR.stop()
		if not self.suppresed:
			self.has_fired = False


	def check(self):
		fire_cond = (read_color_sensor(CS_M) == "black" and read_color_sensor(CS_L) == "black" and read_ultrasonic_sensor(ULT_B) < 10)
		if fire_cond != self.has_fired:
			self.has_fired = fire_cond
			if self.has_fired:
				self.operations = [lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: S.beep(), lambda: MOTOR.turn(direction="RIGHT", degrees=90, speed=30), lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: ARM_MOTOR.move(up=False, rotations=1, block=True), lambda: time.sleep(36000), lambda: ARM_MOTOR.move(up=True, rotations=1, block=True), lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: S.beep(), lambda: MOTOR.turn(direction="RIGHT", degrees=90, speed=30)]
				return True

		return False


	def action(self):
		self.suppresed = False
		if DEBUG:
			timedlog("bd fired")

		for operation in self.operations:
			operation()
			while MOTOR.is_running and not self.supressed:
				pass
			if self.supressed:
				break

		self._reset()

		if DEBUG and not self.supressed:
			timedlog("bd done")
		return not self.supressed


	def suppress(self):
		MOTOR.stop()
		self.supressed = True
		if DEBUG:
			timedlog("bd suppressed")




class ba_bhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.suppresed = False
		self.operations = []
		self.has_fired = False


	def _reset(self):
		self.operations = []
		MOTOR.stop()
		if not self.suppresed:
			self.has_fired = False


	def check(self):
		fire_cond = (read_color_sensor(CS_M) == "black")
		if fire_cond != self.has_fired:
			self.has_fired = fire_cond
			if self.has_fired:
				self.operations = [lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: MOTOR.run(forward=True, distance=10, speed=30)]
				return True

		return False


	def action(self):
		self.suppresed = False
		if DEBUG:
			timedlog("ba fired")

		for operation in self.operations:
			operation()
			while MOTOR.is_running and not self.supressed:
				pass
			if self.supressed:
				break

		self._reset()

		if DEBUG and not self.supressed:
			timedlog("ba done")
		return not self.supressed


	def suppress(self):
		MOTOR.stop()
		self.supressed = True
		if DEBUG:
			timedlog("ba suppressed")




class ma_updateTasksBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		global EXECUTING_STATE
		EXECUTING_STATE = 0
		self.fired = False
		self.timer = 0
		TASK_REGISTRY.add("state_0", 1)
		TASK_REGISTRY.add("state_1", 1)
		self.task_list_cond = [[lambda: read_color_sensor(CS_M) == "black" or readings_dict[TOUCH_L] or read_color_sensor(CS_L) == "black" or read_ultrasonic_sensor(ULT_B) < 10], [lambda: RUNNING_ACTIONS_DONE]]
		self.timeout = [30, 60]

	def check(self):
		global EXECUTING_STATE, RUNNING_ACTIONS_DONE
		if not self.fired:
			if self.timer == 0:
				self.timer = time.time()
			for i in range(len(self.task_list_cond[EXECUTING_STATE])):
				TASK_REGISTRY.update("state_" + str(EXECUTING_STATE), self.task_list_cond[EXECUTING_STATE][i](), i)
			timeouted = self.timer != 0 and time.time() - self.timer > self.timeout[EXECUTING_STATE]
			if TASK_REGISTRY.task_done("state_" + str(EXECUTING_STATE)) or timeouted:
				EXECUTING_STATE += 1
				RUNNING_ACTIONS_DONE = False
				self.timer = 0

				if EXECUTING_STATE == 2:
					self.fired = True
			return timeouted
		return False

	def action(self):
		MOTOR.stop()
		for operation in []:
			operation()

	def suppress(self):
		pass


class ma_RunningBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		global RUNNING_ACTIONS_DONE
		self.counter_action = 0
		RUNNING_ACTIONS_DONE = False
		self.operations = [[lambda: MOTOR.run(forward=True, distance=100, brake=False, speedM=1.3), lambda: (self.counter_action := 0)], [lambda: MOTOR.oddometry_start(), lambda: MOTOR.to_coordinates(0, 20, speed=30), lambda: MOTOR.to_coordinates(10, 20, speed=30), lambda: MOTOR.to_coordinates(10, 20, speed=30), lambda: MOTOR.to_coordinates(31, 41, speed=10), lambda: MOTOR.oddometry_stop()]]

	def check(self):
		global RUNNING_ACTIONS_DONE
		return not TASK_REGISTRY.tasks_done() and not RUNNING_ACTIONS_DONE

	def action(self):
		
		for operation in self.operations[EXECUTING_STATE][self.counter_action:]:
			operation()
			while self.motor.is_running and not self.supressed:
				pass
			if not self.supressed:
				self.counter_action += 1
		
		if self.counter_action == len(self.operations[EXECUTING_STATE]):
			RUNNING_ACTIONS_DONE = True
			self.counter_action = 0
			return True
		return False


	def suppress(self):
		self.motor.stop()
		self.supressed = True
		if DEBUG:
			timedlog("RunningBhv suppressed")
		pass




mission(taskList=[task(timeout=30,activityType="TRIGGER",activityList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(539,2,<29,27>,<29,29>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(543,2,<29,31>,<29,33>)],activityListMod="ANY"),task(timeout=60,activityType="ACTION",activityList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(554,2,<29,42>,<29,44>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(558,2,<29,46>,<29,48>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(562,2,<29,50>,<29,52>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(566,2,<29,54>,<29,56>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(570,3,<29,58>,<29,61>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(575,3,<29,63>,<29,66>)],activityListMod="ALL")],feedbacks=<[],[],[]>,behaviorList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(587,2,<29,75>,<29,77>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(592,2,<29,80>,<29,82>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(597,2,<29,85>,<29,87>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(602,2,<29,90>,<29,92>)])


class mb_updateTasksBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		global EXECUTING_STATE
		EXECUTING_STATE = 0
		self.fired = False
		self.timer = 0
		TASK_REGISTRY.add("state_0", 1)
		self.task_list_cond = [[lambda: RUNNING_ACTIONS_DONE]]
		self.timeout = [60]

	def check(self):
		global EXECUTING_STATE, RUNNING_ACTIONS_DONE
		if not self.fired:
			if self.timer == 0:
				self.timer = time.time()
			for i in range(len(self.task_list_cond[EXECUTING_STATE])):
				TASK_REGISTRY.update("state_" + str(EXECUTING_STATE), self.task_list_cond[EXECUTING_STATE][i](), i)
			timeouted = self.timer != 0 and time.time() - self.timer > self.timeout[EXECUTING_STATE]
			if TASK_REGISTRY.task_done("state_" + str(EXECUTING_STATE)) or timeouted:
				EXECUTING_STATE += 1
				RUNNING_ACTIONS_DONE = False
				self.timer = 0

				if EXECUTING_STATE == 1:
					self.fired = True
			return timeouted
		return False

	def action(self):
		MOTOR.stop()
		for operation in ["S.beep()","S.beep()"]:
			operation()

	def suppress(self):
		pass


class mb_RunningBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		global RUNNING_ACTIONS_DONE
		self.counter_action = 0
		RUNNING_ACTIONS_DONE = False
		self.operations = [[lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE)]]

	def check(self):
		global RUNNING_ACTIONS_DONE
		return not TASK_REGISTRY.tasks_done() and not RUNNING_ACTIONS_DONE

	def action(self):
		
		for operation in self.operations[EXECUTING_STATE][self.counter_action:]:
			operation()
			while self.motor.is_running and not self.supressed:
				pass
			if not self.supressed:
				self.counter_action += 1
		
		if self.counter_action == len(self.operations[EXECUTING_STATE]):
			RUNNING_ACTIONS_DONE = True
			self.counter_action = 0
			return True
		return False


	def suppress(self):
		self.motor.stop()
		self.supressed = True
		if DEBUG:
			timedlog("RunningBhv suppressed")
		pass




mission(taskList=[task(timeout=60,activityType="ACTION",activityList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(627,4,<30,20>,<30,24>)],activityListMod="ALL")],feedbacks=<[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(665,3,<30,58>,<30,61>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(670,2,<30,63>,<30,65>)],[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(680,2,<30,73>,<30,75>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(684,2,<30,77>,<30,79>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(688,3,<30,81>,<30,84>)],[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(703,2,<30,96>,<30,98>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(707,2,<30,100>,<30,102>)]>,behaviorList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(639,2,<30,32>,<30,34>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(643,2,<30,36>,<30,38>)])


class md_updateTasksBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		global EXECUTING_STATE
		EXECUTING_STATE = 0
		self.fired = False
		self.timer = 0
		TASK_REGISTRY.add("state_0", 1)
		TASK_REGISTRY.add("state_1", 1)
		self.task_list_cond = [[lambda: read_color_sensor(CS_M) == "black"], [lambda: read_color_sensor(CS_L) == "black"]]
		self.timeout = [60, 60]

	def check(self):
		global EXECUTING_STATE, RUNNING_ACTIONS_DONE
		if not self.fired:
			if self.timer == 0:
				self.timer = time.time()
			for i in range(len(self.task_list_cond[EXECUTING_STATE])):
				TASK_REGISTRY.update("state_" + str(EXECUTING_STATE), self.task_list_cond[EXECUTING_STATE][i](), i)
			timeouted = self.timer != 0 and time.time() - self.timer > self.timeout[EXECUTING_STATE]
			if TASK_REGISTRY.task_done("state_" + str(EXECUTING_STATE)) or timeouted:
				EXECUTING_STATE += 1
				RUNNING_ACTIONS_DONE = False
				self.timer = 0

				if EXECUTING_STATE == 2:
					self.fired = True
			return timeouted
		return False

	def action(self):
		MOTOR.stop()
		for operation in []:
			operation()

	def suppress(self):
		pass


class md_RunningBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		global RUNNING_ACTIONS_DONE
		self.counter_action = 0
		RUNNING_ACTIONS_DONE = False
		self.operations = [[lambda: MOTOR.run(forward=True, distance=100, brake=False, speedM=1.3), lambda: (self.counter_action := 0)], [lambda: MOTOR.run(forward=True, distance=100, brake=False, speedM=1.3), lambda: (self.counter_action := 0)]]

	def check(self):
		global RUNNING_ACTIONS_DONE
		return not TASK_REGISTRY.tasks_done() and not RUNNING_ACTIONS_DONE

	def action(self):
		
		for operation in self.operations[EXECUTING_STATE][self.counter_action:]:
			operation()
			while self.motor.is_running and not self.supressed:
				pass
			if not self.supressed:
				self.counter_action += 1
		
		if self.counter_action == len(self.operations[EXECUTING_STATE]):
			RUNNING_ACTIONS_DONE = True
			self.counter_action = 0
			return True
		return False


	def suppress(self):
		self.motor.stop()
		self.supressed = True
		if DEBUG:
			timedlog("RunningBhv suppressed")
		pass




mission(taskList=[task(timeout=60,activityType="TRIGGER",activityList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(785,2,<32,22>,<32,24>)],activityListMod="ALL"),task(timeout=60,activityType="TRIGGER",activityList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(791,2,<32,28>,<32,30>)],activityListMod="ALL")],feedbacks=<[],[],[]>,behaviorList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(803,2,<32,40>,<32,42>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(807,2,<32,44>,<32,46>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(811,2,<32,48>,<32,50>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(815,2,<32,52>,<32,54>)])


class mf_updateTasksBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		global EXECUTING_STATE
		EXECUTING_STATE = 0
		self.fired = False
		self.timer = 0
		TASK_REGISTRY.add("state_0", 1)
		self.task_list_cond = [[lambda: read_color_sensor(CS_M) == "black"]]
		self.timeout = [60]

	def check(self):
		global EXECUTING_STATE, RUNNING_ACTIONS_DONE
		if not self.fired:
			if self.timer == 0:
				self.timer = time.time()
			for i in range(len(self.task_list_cond[EXECUTING_STATE])):
				TASK_REGISTRY.update("state_" + str(EXECUTING_STATE), self.task_list_cond[EXECUTING_STATE][i](), i)
			timeouted = self.timer != 0 and time.time() - self.timer > self.timeout[EXECUTING_STATE]
			if TASK_REGISTRY.task_done("state_" + str(EXECUTING_STATE)) or timeouted:
				EXECUTING_STATE += 1
				RUNNING_ACTIONS_DONE = False
				self.timer = 0

				if EXECUTING_STATE == 1:
					self.fired = True
			return timeouted
		return False

	def action(self):
		MOTOR.stop()
		for operation in ["S.beep()"]:
			operation()

	def suppress(self):
		pass


class mf_RunningBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		global RUNNING_ACTIONS_DONE
		self.counter_action = 0
		RUNNING_ACTIONS_DONE = False
		self.operations = [[lambda: MOTOR.run(forward=True, distance=100, brake=False, speedM=1.3), lambda: (self.counter_action := 0)]]

	def check(self):
		global RUNNING_ACTIONS_DONE
		return not TASK_REGISTRY.tasks_done() and not RUNNING_ACTIONS_DONE

	def action(self):
		
		for operation in self.operations[EXECUTING_STATE][self.counter_action:]:
			operation()
			while self.motor.is_running and not self.supressed:
				pass
			if not self.supressed:
				self.counter_action += 1
		
		if self.counter_action == len(self.operations[EXECUTING_STATE]):
			RUNNING_ACTIONS_DONE = True
			self.counter_action = 0
			return True
		return False


	def suppress(self):
		self.motor.stop()
		self.supressed = True
		if DEBUG:
			timedlog("RunningBhv suppressed")
		pass




mission(taskList=[task(timeout=60,activityType="TRIGGER",activityList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(841,2,<33,21>,<33,23>)],activityListMod="ALL")],feedbacks=<[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(872,2,<33,52>,<33,54>)],[],[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(891,2,<33,71>,<33,73>)]>,behaviorList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(851,2,<33,31>,<33,33>)])


CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(ma_updateTasksBhv())

CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
CONTROLLER.add(bc_bhv())
CONTROLLER.add(bd_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start') # REMOVE BEFORE DELIVERY

for operation in []:
	operation()

if DEBUG:
	timedlog("Starting")
CONTROLLER.run()


for operation in []:
	operation()





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(mb_updateTasksBhv())

CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start') # REMOVE BEFORE DELIVERY

for operation in [lambda: S.speak("Hello World", play_type=S.PLAY_WAIT_FOR_COMPLETE), lambda: S.beep()]:
	operation()

if DEBUG:
	timedlog("Starting")
CONTROLLER.run()


for operation in [lambda: S.beep(), lambda: S.beep(), lambda: feedback_leds_blocking(LEDS, "GREEN")]:
	operation()





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(ma_updateTasksBhv())

CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
CONTROLLER.add(bc_bhv())
CONTROLLER.add(bd_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start') # REMOVE BEFORE DELIVERY

for operation in []:
	operation()

if DEBUG:
	timedlog("Starting")
CONTROLLER.run()


for operation in []:
	operation()





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(mb_updateTasksBhv())

CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start') # REMOVE BEFORE DELIVERY

for operation in [lambda: S.speak("Hello World", play_type=S.PLAY_WAIT_FOR_COMPLETE), lambda: S.beep()]:
	operation()

if DEBUG:
	timedlog("Starting")
CONTROLLER.run()


for operation in [lambda: S.beep(), lambda: S.beep(), lambda: feedback_leds_blocking(LEDS, "GREEN")]:
	operation()





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(md_updateTasksBhv())

CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
CONTROLLER.add(bd_bhv())
CONTROLLER.add(bc_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start') # REMOVE BEFORE DELIVERY

for operation in []:
	operation()

if DEBUG:
	timedlog("Starting")
CONTROLLER.run()


for operation in []:
	operation()





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(mf_updateTasksBhv())

CONTROLLER.add(ba_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start') # REMOVE BEFORE DELIVERY

for operation in [lambda: S.beep()]:
	operation()

if DEBUG:
	timedlog("Starting")
CONTROLLER.run()


for operation in []:
	operation()





