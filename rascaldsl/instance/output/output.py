

"211"

[|file:///h:/Altri%20computer/Il%20mio%20laptop/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(527,2,<27,76>,<27,78>),|file:///h:/Altri%20computer/Il%20mio%20laptop/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(532,2,<27,81>,<27,83>),|file:///h:/Altri%20computer/Il%20mio%20laptop/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(537,2,<27,86>,<27,88>),|file:///h:/Altri%20computer/Il%20mio%20laptop/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(522,2,<27,71>,<27,73>)]


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
		EXECUTING_STATE = 0
		self.fired = False
		TASK_REGISTRY.add("state_0", 1)
		TASK_REGISTRY.add("state_1", 1)
		self.task_list_cond = [[lambda: read_color_sensor(CS_L) == "black" or read_color_sensor(CS_M) == "black" or readings_dict["ULT_F"] < 10 or readings_dict[TOUCH_L]], [lambda: RUNNING_ACTIONS_DONE]]

	def check(self):
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
		self.counter_action = 0
		RUNNING_ACTIONS_DONE = False
		self.operations = [[lambda: ()], [lambda: MOTOR.oddometry_start(), lambda: MOTOR.to_coordinates(0, 20, speed=30), lambda: MOTOR.to_coordinates(10, 20, speed=30), lambda: MOTOR.to_coordinates(10, 20, speed=30), lambda: MOTOR.to_coordinates(31, 41, speed=10), lambda: MOTOR.oddometry_stop()]]

	def check(self):
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





class mb_updateTasksBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		EXECUTING_STATE = 0
		self.fired = False
		TASK_REGISTRY.add("state_0", 1)
		self.task_list_cond = [[lambda: read_color_sensor(CS_M) == "black"]]

	def check(self):
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
		self.counter_action = 0
		RUNNING_ACTIONS_DONE = False
		self.operations = [[lambda: ()]]

	def check(self):
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





class md_updateTasksBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		EXECUTING_STATE = 0
		self.fired = False
		TASK_REGISTRY.add("state_0", 1)
		TASK_REGISTRY.add("state_1", 1)
		self.task_list_cond = [[lambda: read_color_sensor(CS_M) == "black"], [lambda: read_color_sensor(CS_L) == "black"]]

	def check(self):
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
		self.counter_action = 0
		RUNNING_ACTIONS_DONE = False
		self.operations = [[lambda: ()], [lambda: ()]]

	def check(self):
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





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(ma_updateTasksBhv())

CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
CONTROLLER.add(bc_bhv())
CONTROLLER.add(bd_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start')
if DEBUG:
	timedlog("Starting")
CONTROLLER.run()





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(mb_updateTasksBhv())

CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start')
if DEBUG:
	timedlog("Starting")
CONTROLLER.run()





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(ma_updateTasksBhv())

CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
CONTROLLER.add(bc_bhv())
CONTROLLER.add(bd_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start')
if DEBUG:
	timedlog("Starting")
CONTROLLER.run()





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(mb_updateTasksBhv())

CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start')
if DEBUG:
	timedlog("Starting")
CONTROLLER.run()





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(md_updateTasksBhv())

CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
CONTROLLER.add(bd_bhv())
CONTROLLER.add(bc_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start')
if DEBUG:
	timedlog("Starting")
CONTROLLER.run()





