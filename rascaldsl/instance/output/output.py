

"211"

[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(571,2,<28,76>,<28,78>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(576,2,<28,81>,<28,83>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(581,2,<28,86>,<28,88>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(566,2,<28,71>,<28,73>)]


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
		fire_cond = (read_color_sensor(CS_L) == "black" and read_color_sensor(CS_M) == "black" and readings_dict["ULT_F"] < 10 and readings_dict[TOUCH_L])
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
		fire_cond = (read_color_sensor(CS_L) == "black" or read_color_sensor(CS_M) == "black" or readings_dict["ULT_F"] < 10)
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
		fire_cond = (read_color_sensor(CS_L) == "black" and read_color_sensor(CS_M) == "black" and readings_dict["ULT_F"] < 10)
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
				self.operations = [lambda: MOTOR.run(forward=True, distance=10, speed=30)]
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
		TASK_REGISTRY.add("state_0", 1)
		TASK_REGISTRY.add("state_1", 1)
		self.task_list_cond = [[lambda: read_color_sensor(CS_L) == "black" or read_color_sensor(CS_M) == "black" or readings_dict["ULT_F"] < 10 or readings_dict[TOUCH_L]], [lambda: RUNNING_ACTIONS_DONE]]

	def check(self):
		global EXECUTING_STATE, RUNNING_ACTIONS_DONE
		if not self.fired:
			for i in range(len(self.task_list_cond[EXECUTING_STATE])):
				TASK_REGISTRY.update("state_" + str(EXECUTING_STATE), self.task_list_cond[EXECUTING_STATE][i](), i)
			if TASK_REGISTRY.task_done("state_" + str(EXECUTING_STATE)):
				EXECUTING_STATE += 1
				RUNNING_ACTIONS_DONE = False

			if EXECUTING_STATE == 2:
				self.fired = True
				return True
		return False

	def action(self):
		return True

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




mission(taskList=[task(activityType="TRIGGER",activityList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(522,2,<28,27>,<28,29>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(526,2,<28,31>,<28,33>)],activityListMod="ANY"),task(activityType="ACTION",activityList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(533,2,<28,38>,<28,40>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(537,2,<28,42>,<28,44>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(541,2,<28,46>,<28,48>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(545,2,<28,50>,<28,52>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(549,3,<28,54>,<28,57>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(554,3,<28,59>,<28,62>)],activityListMod="ALL")],feedbacks=<[],[],[]>,behaviorList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(566,2,<28,71>,<28,73>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(571,2,<28,76>,<28,78>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(576,2,<28,81>,<28,83>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(581,2,<28,86>,<28,88>)])


class mb_updateTasksBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		global EXECUTING_STATE
		EXECUTING_STATE = 0
		self.fired = False
		TASK_REGISTRY.add("state_0", 1)
		self.task_list_cond = [[lambda: read_color_sensor(CS_M) == "black"]]

	def check(self):
		global EXECUTING_STATE, RUNNING_ACTIONS_DONE
		if not self.fired:
			for i in range(len(self.task_list_cond[EXECUTING_STATE])):
				TASK_REGISTRY.update("state_" + str(EXECUTING_STATE), self.task_list_cond[EXECUTING_STATE][i](), i)
			if TASK_REGISTRY.task_done("state_" + str(EXECUTING_STATE)):
				EXECUTING_STATE += 1
				RUNNING_ACTIONS_DONE = False

			if EXECUTING_STATE == 1:
				self.fired = True
				return True
		return False

	def action(self):
		return True

	def suppress(self):
		pass


class mb_RunningBhv(Behavior):
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




mission(taskList=[task(activityType="TRIGGER",activityList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(607,2,<29,21>,<29,23>)],activityListMod="ALL")],feedbacks=<[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(644,3,<29,58>,<29,61>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(649,2,<29,63>,<29,65>)],[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(659,2,<29,73>,<29,75>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(663,2,<29,77>,<29,79>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(667,3,<29,81>,<29,84>)],[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(682,2,<29,96>,<29,98>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(686,2,<29,100>,<29,102>)]>,behaviorList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(618,2,<29,32>,<29,34>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(622,2,<29,36>,<29,38>)])


class md_updateTasksBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		global EXECUTING_STATE
		EXECUTING_STATE = 0
		self.fired = False
		TASK_REGISTRY.add("state_0", 1)
		TASK_REGISTRY.add("state_1", 1)
		self.task_list_cond = [[lambda: read_color_sensor(CS_M) == "black"], [lambda: read_color_sensor(CS_L) == "black"]]

	def check(self):
		global EXECUTING_STATE, RUNNING_ACTIONS_DONE
		if not self.fired:
			for i in range(len(self.task_list_cond[EXECUTING_STATE])):
				TASK_REGISTRY.update("state_" + str(EXECUTING_STATE), self.task_list_cond[EXECUTING_STATE][i](), i)
			if TASK_REGISTRY.task_done("state_" + str(EXECUTING_STATE)):
				EXECUTING_STATE += 1
				RUNNING_ACTIONS_DONE = False

			if EXECUTING_STATE == 2:
				self.fired = True
				return True
		return False

	def action(self):
		return True

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




mission(taskList=[task(activityType="TRIGGER",activityList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(764,2,<31,22>,<31,24>)],activityListMod="ALL"),task(activityType="TRIGGER",activityList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(770,2,<31,28>,<31,30>)],activityListMod="ALL")],feedbacks=<[],[],[]>,behaviorList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(782,2,<31,40>,<31,42>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(786,2,<31,44>,<31,46>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(790,2,<31,48>,<31,50>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(794,2,<31,52>,<31,54>)])


class mf_updateTasksBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		global EXECUTING_STATE
		EXECUTING_STATE = 0
		self.fired = False
		TASK_REGISTRY.add("state_0", 1)
		self.task_list_cond = [[lambda: read_color_sensor(CS_M) == "black"]]

	def check(self):
		global EXECUTING_STATE, RUNNING_ACTIONS_DONE
		if not self.fired:
			for i in range(len(self.task_list_cond[EXECUTING_STATE])):
				TASK_REGISTRY.update("state_" + str(EXECUTING_STATE), self.task_list_cond[EXECUTING_STATE][i](), i)
			if TASK_REGISTRY.task_done("state_" + str(EXECUTING_STATE)):
				EXECUTING_STATE += 1
				RUNNING_ACTIONS_DONE = False

			if EXECUTING_STATE == 1:
				self.fired = True
				return True
		return False

	def action(self):
		return True

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




mission(taskList=[task(activityType="TRIGGER",activityList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(820,2,<32,21>,<32,23>)],activityListMod="ALL")],feedbacks=<[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(851,2,<32,52>,<32,54>)],[],[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(870,2,<32,71>,<32,73>)]>,behaviorList=[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(830,2,<32,31>,<32,33>)])


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

for operation in [lambda: S.speak(""Hello World"", play_type=S.PLAY_WAIT_FOR_COMPLETE), lambda: S.beep()]:
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

for operation in [lambda: S.speak(""Hello World"", play_type=S.PLAY_WAIT_FOR_COMPLETE), lambda: S.beep()]:
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





