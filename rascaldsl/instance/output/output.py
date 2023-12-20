
"211"

[|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(465,2,<26,44>,<26,46>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(469,2,<26,48>,<26,50>),|file:///c:/programmazione/dsl_project/final/embedded-systems/rascaldsl/instance/spec1.tdsl|(461,2,<26,40>,<26,42>)]


class bb(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.has_fired = False
		self.suppresed = False

	def check(self):
		self.has_fired = colorTrigger(color="black",sensor="mid")
		return self.has_fired

	def action(self):
		self.suppresed = False
		[lambda: moveAction(distance=10,direction="forward"), lambda: speakAction(text="&.&.&.")]





("ta":["colorTrigger(color=\"black\",sensor=\"mid\")"])
("aa":["moveAction(distance=10,direction=\"forward\")"],"ac":["speakAction(text=\"&.&.&.\")"])




class bd(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.has_fired = False
		self.suppresed = False

	def check(self):
		self.has_fired = colorTrigger(color="black",sensor="left") or distanceTrigger(distance=10,sensor="front") or colorTrigger(color="black",sensor="mid")
		return self.has_fired

	def action(self):
		self.suppresed = False
		[lambda: moveAction(distance=10,direction="forward"), lambda: speakAction(text="&.&.&."), lambda: moveAction(distance=10,direction="forward")]





("ta":["colorTrigger(color=\"black\",sensor=\"mid\")"],"tb":["colorTrigger(color=\"black\",sensor=\"left\")"],"tc":["distanceTrigger(distance=10,sensor=\"front\")"],"td":["colorTrigger(color=\"black\",sensor=\"mid\")","distanceTrigger(distance=10,sensor=\"front\")","colorTrigger(color=\"black\",sensor=\"left\")"])
("aa":["moveAction(distance=10,direction=\"forward\")"],"ac":["speakAction(text=\"&.&.&.\")"],"ad":["moveAction(distance=10,direction=\"forward\")","speakAction(text=\"&.&.&.\")"])




class ba(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.has_fired = False
		self.suppresed = False

	def check(self):
		self.has_fired = colorTrigger(color="black",sensor="mid")
		return self.has_fired

	def action(self):
		self.suppresed = False
		[lambda: moveAction(distance=10,direction="forward")]





("ta":["colorTrigger(color=\"black\",sensor=\"mid\")"],"tb":["colorTrigger(color=\"black\",sensor=\"left\")"],"tc":["distanceTrigger(distance=10,sensor=\"front\")"],"td":["colorTrigger(color=\"black\",sensor=\"mid\")","distanceTrigger(distance=10,sensor=\"front\")","colorTrigger(color=\"black\",sensor=\"left\")"])
("aa":["moveAction(distance=10,direction=\"forward\")"],"ac":["speakAction(text=\"&.&.&.\")"],"ad":["moveAction(distance=10,direction=\"forward\")","speakAction(text=\"&.&.&.\")"])



