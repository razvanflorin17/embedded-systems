
"211"

[|file:///h:/Altri%20computer/Il%20mio%20laptop/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(420,2,<25,34>,<25,36>),|file:///h:/Altri%20computer/Il%20mio%20laptop/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(416,2,<25,30>,<25,32>)]


class bb_bhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.suppresed = False
		self.operations = []
		self.has_fired = False
		self.counter_conds = 0
		self.trigger_list = [lambda: read_color_sensor(CS_M) == "black", lambda: read_color_sensor(CS_M) == "black"]


	def _reset(self):
		self.operations = []
		MOTOR.stop()
		if not self.suppresed:
			self.has_fired = False
			self.counter_conds = 0
			self.trigger_list = [lambda: read_color_sensor(CS_M) == "black", lambda: read_color_sensor(CS_M) == "black"]


	def check(self):
		
		if self.trigger_list[self.counter_conds]():
			self.counter_conds += 1
		if self.counter_conds == 2:
			self.operations = [lambda: MOTOR.run(forward=True, distance=1, speed=30), lambda: S.beep()]
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
				self.operations = [lambda: MOTOR.run(forward=True, distance=1, speed=30)]
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




class mb_updateTasksBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		TASK_REGISTRY.add("state_1 ")

	def check(self):
		TASK_REGISTRY.update("state_1 ", (read_color_sensor(CS_M) == "black"))
		return False

	def action(self):
		return True

	def suppress(self):
		pass


class ma_updateTasksBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		TASK_REGISTRY.add("state_1 ")

	def check(self):
		TASK_REGISTRY.update("state_1 ", (read_color_sensor(CS_M) == "black"))
		return False

	def action(self):
		return True

	def suppress(self):
		pass


class mc_updateTasksBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		TASK_REGISTRY.add("ALLORD")
		self.counter_task = 0
		self.task_list = [lambda: read_color_sensor(CS_M) == "black", lambda: readings_dict["ULT_F"] < 10, lambda: read_color_sensor(CS_L) == "black"]

	def check(self):
		
		if self.task_list[self.counter_task]():
			self.counter_task += 1
		if self.counter_task == 3:
			TASK_REGISTRY.update("ALLORD", True)

		return False

	def action(self):
		return True

	def suppress(self):
		pass



CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(mb_updateTasksBhv())

CONTROLLER.add(bb_bhv())
CONTROLLER.add(ba_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start')
if DEBUG:
	timedlog("Starting")
CONTROLLER.run()





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(ma_updateTasksBhv())

CONTROLLER.add(bb_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start')
if DEBUG:
	timedlog("Starting")
CONTROLLER.run()





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()
CONTROLLER.add(mc_updateTasksBhv())

CONTROLLER.add(ba_bhv())
bluetooth_connection.start_listening(lambda data: ())
s.speak('Start')
if DEBUG:
	timedlog("Starting")
CONTROLLER.run()





