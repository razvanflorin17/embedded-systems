module Static_Generator

tuple[str, str] static_code_generator() {
    rVal = "#!/usr/bin/env python3
    # -*- coding: utf-8 -*-
    import threading


    class Behavior(object):
        \"\"\"
        This is an abstract class. Should embody an specific behavior belonging to a robot. Each Behavior must define three
        things and should be implemented by the user:
        1. check: Under what circumcises should this behavior take control.
        2. action: What should this behavior do while it has control.
        3. suppress: Should give up control immediately when this method is called. Will be called when a behavior with a
        higher priority wants to take control.
        \"\"\"

        def check(self):
            \"\"\"
            Method to check whether if this behavior should be started or not.
            @return: Should return a true value if this behavior should take control or not
            \"\"\"
            raise NotImplementedError(\"Should have implemented this\")

        def action(self):
            \"\"\"
            The code in action should represent what the behavior should do while it\'s active. When this method returns
            the action is complete and the robot should be in a complete safe state, ie the motors are shut down and such,
            so the next behavior can take safely take control of the robot
            \"\"\"
            raise NotImplementedError(\"Should have implemented this\")

        def suppress(self):
            \"\"\"
            Should immediately cause the behavior to exits it execution and put the state in safe mode. In other words it
            should cause the action() method to stop it\'s execution
            \"\"\"
            raise NotImplementedError(\"Should have implemented this\")


    class Controller():
        \"\"\"
        Runs the main subsumption logic. Controls which behavior will run based on their priority and if they want to become
        active or not. Works as a scheduler, where only one behavior can be active at a time and who is active is decided by
        the sensor data and their priority. The previous active behavior gets suppressed when a behavior with a higher
        priority wants to run.

        There is two usages in this class. One is to make the class take care of scheduler itself, by calling the start()
        method. The other is to take care of the scheduler by yourself, by using the step() method
        \"\"\"

        def __init__(self, return_when_no_action):
            \"\"\"
            Initialize the object. Notice the subsumption module is not bound to a specific brick, the behaviors are. This
            makes it possible to have a subsumption module responsible for multiple bricks at the same time, if desirable.
            \"\"\"
            self.behaviors = []
            self.wait_object = threading.Event()
            self.active_behavior_index = None

            self._running = True
            self._return_when_no_action = return_when_no_action

            self.callback = lambda x: 0

        def add(self, behavior):
            \"\"\"
            Add a behavior to the behavior module. The order decide which priority they have. First \> Second
            @type behavior: Behavior
            \"\"\"
            self.behaviors.append(behavior)

        def remove(self, index):
            old_behavior = self.behaviors[index]
            del self.behaviors[index]
            if self.active_behavior_index == index:  # stop the old one if the new one overrides it
                old_behavior.suppress()
                self.active_behavior_index = None

        def update(self, behavior, index):
            old_behavior = self.behaviors[index]
            self.behaviors[index] = behavior
            if self.active_behavior_index == index:  # stop the old one if the new one overrides it
                old_behavior.suppress()

        def step(self):
            \"\"\"
            Find the next active behavior and runs it.
            @return: Returns whether it got to run any behavior or not
            \"\"\"
            behavior = self.find_next_active_behavior()
            if behavior is not None:
                self.behaviors[behavior].action()
                return True
            return False

        def find_next_active_behavior(self):
            \"\"\"
            Finds the next behavior that wants to run, if any
            @return: Next runnable behavior if any
            @rtype: int
            \"\"\"
            for priority, behavior in enumerate(self.behaviors):
                if behavior.check():
                    return priority
            return None

        def _find_and_set_new_active_behavior(self):
            new_behavior_priority = self.find_next_active_behavior()
            if self.active_behavior_index is None or self.active_behavior_index \> new_behavior_priority:
                if self.active_behavior_index is not None:
                    self.behaviors[self.active_behavior_index].suppress()
                self.active_behavior_index = new_behavior_priority

                # Callback to tell something it changed the active behavior if anything is interested
                self.callback(self.active_behavior_index)

        def _start(self):  # run the action methods
            \"\"\"
            Starts finding and running behaviors, suppressing the old behaviors when new behaviors with higher priority
            wants to run.
            \"\"\"
            self._running = True
            self._find_and_set_new_active_behavior()  # force do it ourselves once to find the right one
            thread = threading.Thread(name=\"Continuous behavior checker\",
                                    target=self._continuously_find_new_active_behavior, args=())
            thread.daemon = True
            thread.start()

            while self._running:
                if self.active_behavior_index is not None:
                    running_behavior = self.active_behavior_index
                    self.behaviors[running_behavior].action()
                    if running_behavior == self.active_behavior_index:  # means the action got completed the old fashion way
                        self.active_behavior_index = None
                        self._find_and_set_new_active_behavior()

                elif self._return_when_no_action:
                    break

            #Nothing more to do, so we are shutting down
            self._running = False

        def start(self, run_in_thread=False):
            if run_in_thread:
                thread = threading.Thread(name=\"Subsumption Thread\",
                                        target=self._start, args=())
                thread.daemon = True
                thread.start()
            else:
                self._start()

        def stop(self):
            self._running = False
            self.behaviors[self.active_behavior_index].suppress()

        def _continuously_find_new_active_behavior(self):
            while self._running:
                self._find_and_set_new_active_behavior()

        def __str__(self):
            return str(self.behaviors)

    DEBUG = False


    from ev3dev2.motor import SpeedPercent, MoveDifferential, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
    from ev3dev2.display import Display
    from ev3dev2.wheel import EV3EducationSetTire
    from ev3dev2.sound import Sound
    from ev3dev2.led import Leds
    from ev3dev2.sensor.lego import ColorSensor, TouchSensor, UltrasonicSensor
    from ev3dev2._platform.ev3 import INPUT_1, INPUT_2, INPUT_3, INPUT_4
    import bluetooth, threading, random, time
    if DEBUG:
        from ev3devlogging import timedlog

    SOUND_NO_BLOCK = Sound.PLAY_NO_WAIT_FOR_COMPLETE # sound option that doesn\'t block the program
    BASE_SPEED = 20
    LEFT, RIGHT = -1, 1
    BLACK = 1

    def int2color(colornr):
        color_dict = {0: \"nocolor\", 1: \"black\", 2: \"blue\", 3: \"green\", 4: \"yellow\", 5: \"red\", 6: \"white\", 7: \"brown\"}
        return color_dict[colornr]


    def set_leds_color(leds, color):
        if color not in [\"BLACK\", \"RED\", \"GREEN\", \"AMBER\", \"ORANGE\", \"YELLOW\"]:
        color = \"AMBER\"
        leds.set_color(\"LEFT\", color) 
        leds.set_color(\"RIGHT\", color)


    def feedback_leds_blocking(leds, color): # for generated code
        set_leds_color(leds, color)
        time.sleep(0.5)
        leds.reset()


    class ArmMotor():
        \"\"\"
        Wrapper class for the motor, all beahviors should use this class to control the motor.
        In the future if we want to change the type of motor, we only have to change this class
        \"\"\"
        def __init__(self, motor, base_speed=BASE_SPEED):
            self.motor = motor
            self.base_speed = base_speed
        
        def move(self, up=True, rotations=1, speed=None, block=False):
            if speed is None:
                speed = self.base_speed
            if up:
                self.motor.on_for_rotations(SpeedPercent(speed), rotations, block=block)
            else:
                self.motor.on_for_rotations(SpeedPercent(-speed), rotations, block=block)

        def stop(self):
            self.motor.stop()

        @property
        def is_running(self):
            return self.motor.is_running


    class Motor():
        \"\"\"
        Wrapper class for the differential motor, all beahviors should use this class to control the motor.
        In the future if we want to change the type of motor, we only have to change this class
        \"\"\"
        def __init__(self, motor, base_speed=BASE_SPEED):
            self.motor = motor
            self.base_speed = base_speed
            # self.log_distance = 0
            # self.log_angle = 0

        def run(self, forward=True, distance=10, speed=None, speedM=None, block=False, brake=False):
            \"\"\"Runs the motor for a certain distance (cm)\"\"\"
            if speedM is None:
                speedM = 1 if forward else 0.5
            if speed is None:
                speed = self.base_speed * speedM
            if forward:
                self.motor.on_for_distance(SpeedPercent(speed), distance*10, block=block, brake=brake)
            else:
                self.motor.on_for_distance(SpeedPercent(-speed), distance*10, block=block, brake=brake)




        def turn(self, direction=None, degrees=180, speed=None, speedM=0.5, block=False, brake=False):
            if speed is None:
                speed = self.base_speed * speedM

            if direction == None:
                random_direction = random.choice([LEFT, RIGHT])
                self.turn(direction=random_direction, degrees=degrees, speed=speed, speedM=speedM, block=block, brake=brake)
            
            elif direction == RIGHT:
                self.motor.turn_right(SpeedPercent(speed), degrees, block=block, brake=brake)
            else:
                self.motor.turn_left(SpeedPercent(speed), degrees, block=block, brake=brake)


        def stop(self):
            self.motor.stop()

        def odometry_start(self):
            self.motor.odometry_start()
        
        def odometry_stop(self):
            self.motor.odometry_stop()
        
        def to_coordinates(self, x, y, speed=None, speedM=0.5, block=False, brake=False):
            if speed is None:
                speed = self.base_speed * speedM
            self.motor.to_coordinates(x, y, SpeedPercent(speed), block=block, brake=brake)

        @property
        def is_running(self):
            return self.motor.is_running
            
    # class Motor():
    #     \"\"\"
    #     Wrapper class for the steering motor, all beahviors should use this class to control the motor.
    #     In the future if we want to change the type of motor, we only have to change this class
    #     \"\"\"
    #     def __init__(self, motor, base_speed=BASE_SPEED):
    #         self.motor = motor
    #         self.base_speed = base_speed
        
    #     def run(self, forward=True, rotations=1, speed=None, block=False):
    #         if speed is None:
    #             speed = self.base_speed

    #         if forward:
    #             self.motor.on_for_rotations(0, SpeedPercent(speed), rotations, block=block)
    #         else:
    #             self.motor.on_for_rotations(0, SpeedPercent(-speed), rotations, block=block)

    #     def turn(self, direction=None, steer_degrees=180, speed=None, block=False):
    #         if speed is None:
    #             speed = self.base_speed
    #         self.motor.on_for_degrees(direction * 100, SpeedPercent(speed), steer_degrees, block=block)

        
        



    class TaskRegistry():
        \"\"\"
        Class to keep track of tasks that have to be done before the robot can stop.

        Before starting the robot, the main program should add all the tasks that have to be done, 
        so the RunningBhv will check the registry to see if all tasks are done, and if so, stop the robot.
        \"\"\"
        def __init__(self):
            self.tasks = {}

        def add(self, task_name, n_trigger=1):
            self.tasks[task_name] = [False] * n_trigger

        def set(self, task_name, value, trigger_index=0):
            self.tasks[task_name][trigger_index] = value

        def update(self, task_name, value, trigger_index=0):
            self.tasks[task_name][trigger_index] = max(self.tasks[task_name][trigger_index], value)

        def get(self, task_name, trigger_index=0):
            return self.tasks[task_name][trigger_index] if trigger_index is not None else self.tasks[task_name]
        
        def task_done(self, task_name):
            return all(self.tasks[task_name].values())

        def all_tasks_done(self):
            return all([self.task_done(task_name) for task_name in self.tasks])
        
        def reset(self):
            self.tasks = {}


    class BluetoothConnection():
        \"\"\"
        Class to handle the bluetooth connection between the master and the slave.
        \"\"\"
        def __init__(self, is_master, server_mac, port=3, debug=False):
            \"\"\"
            Initializes the socks for the connection.
            @param is_master: True if this brick is the master, False if it\'s the slave
            @param server_mac: The mac address of the master brick
            @param port: The port to use for the connection
            @param debug: Whether to print debug messages or not
            \"\"\"

            self.is_master = is_master
            self.server_mac = server_mac
            self.port = port
            self.debug = debug
            self.buffer = [\"\"] # buffer for the data that is received
            
            self.startup()

        def startup(self):
            \"\"\"
            Starts the connection between the master and the slave.
            \"\"\"
            if self.is_master:
                self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                self.server_sock.bind((self.server_mac, self.port))
                self.server_sock.listen(20)
                
                if self.debug:
                    timedlog(\'Listening for connections from the slave...\')

                client_sock, address = self.server_sock.accept()
                if self.debug:
                    timedlog(\'Accepted connection\')
                self.client_sock = client_sock

            else:
                time.sleep(6)
                self.client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                if self.debug:
                    timedlog(\"Connecting to the master...\")

                self.client_sock.connect((self.server_mac, self.port))

                
                if self.debug:
                    timedlog(\"Connected to the master\")
            
            self.sock_in = self.client_sock.makefile(\'r\')
            self.sock_out = self.client_sock.makefile(\'w\')
            
        def write(self, data):
            \"\"\"
            Sends data to the other brick.
            @param data: The data to send
            \"\"\"
            self.sock_out.write(str(data) + \"\n\")
            self.sock_out.flush()

        def _read(self):
            \"\"\"
            Reads data from the other brick.
            @return: The data that was readq
            \"\"\"
            data = str(self.sock_in.readline())
            
            return data.replace(\"\n\", \"\")
        
        def _listen(self, procedure):
            \"\"\"
            Listens for data from the other brick.
            @param procedure: The procedure to call when data is received (that take the data as argument)
            \"\"\"
            while True:
                data = self._read()
                self.buffer[0] = str(data)
                procedure(data)
        
        def start_listening(self, procedure):
            \"\"\"
            Starts listening for data from the other brick, by opening a thread.
            @param procedure: The procedure to call when data is received (that take the data as argument)
            \"\"\"

            listener = threading.Thread(target=self._listen, args=[procedure])
            listener.start()

        def get_data(self):
            \"\"\"
            Gets the data that was received from the other brick.
            @return: The data that was received
            \"\"\"
            return self.buffer[0]

        def shutdown(self):
            \"\"\"
            Closes the connection between the master and the slave.
            \"\"\"
            self.sock_in.close()
            self.sock_out.close()
            self.client_sock.close()
            if self.is_master:
                self.server_sock.close()


    def read_touch_sensor(touch_sensor):
        \"\"\"
        Reads the touch sensor and returns the distance.
        @param color_sensor: The touch sensor to read
        @return: The touch that was read
        \"\"\"
        lock = threading.Lock()
        
        with lock:
            try:
                touch = touch_sensor.is_pressed
            except: 
                if DEBUG:
                    timedlog(\"Touch sensor wrong read\")
                return read_touch_sensor(touch_sensor)
            return touch
    def read_color_sensor(cs):  
        \"\"\"
        Reads the color sensor and returns the color that was read.
        @param color_sensor: The color sensor to read
        @return: The color that was read
        \"\"\"
        lock = threading.Lock()
        with lock:
            try:
                color = cs.color
            except: 
                if DEBUG:
                    timedlog(\"Color sensor wrong read\")
                return read_color_sensor(cs)
            return int2color(color)

    def read_ultrasonic_sensor(ultrasonic_sensor):
        \"\"\"
        Reads the ultrasonic sensor and returns the distance.
        @param color_sensor: The ultrasonic sensor to read
        @return: The distance that was read
        \"\"\"
        lock = threading.Lock()
        with lock:
            try:
                distance = ultrasonic_sensor.value()
            except: 
                if DEBUG:
                    timedlog(\"Ultrasonic sensor wrong read\")
                return read_ultrasonic_sensor(ultrasonic_sensor)
            return distance




    class RunningBhv(Behavior):
        \"\"\"
        Default behavior that will run if no other behavior is running, to keep the robot moving while its completing tasks
        \"\"\"
        
        def __init__(self, motor, leds=False, task_registry=None):
            \"\"\"
            Initialize the behavior
            @param motor: the motor to use
            @param leds: the leds to use
            @param task_registry: the task registry to check
            \"\"\"
            Behavior.__init__(self)
            self.supressed = False
            self.motor = motor
            self.leds = leds
            self.task_registry = task_registry

        def check(self):
            \"\"\"
            Always returns true if it has task to complete
            @return: True
            @rtype: bool
            \"\"\"
            if self.task_registry is None:
                return True

            return not self.task_registry.tasks_done()

        def action(self):
            \"\"\"
            Keep the robot moving
            \"\"\"

            self.supressed = False
            if DEBUG:
                timedlog(\"Moving\")
            
            # while not self.supressed:
            #     self.motor.run(forward=True, distance=10, brake=False)
            #     while self.motor.is_running and not self.supressed:
            #         pass
            #     if not self.supressed:
            #         self.motor.apply_momentum()

            self.motor.run(forward=True, distance=1000, brake=False, speedM=1.3)
            while self.motor.is_running and not self.supressed:
                pass

            return not self.supressed


        def suppress(self):
            \"\"\"
            Suppress the behavior
            \"\"\"
            self.motor.stop()
            self.supressed = True
            if DEBUG:
                timedlog(\"Moving suppressed\")


    class CliffAvoidanceBhv(Behavior):
        \"\"\"
        This behavior will check if the robot is on falling off the cliff
        \"\"\"

        def __init__(self, back_ult, motor, leds=False, sound=False, heigth_treshold=60):
            \"\"\"
            Initialize the behavior
            @param back_ult: The back ultrasonic sensor to use
            @param motor: the motor to use
            @param leds: the leds to use
            @param sound: the sound to use
            @param heigth_treshold: The treshold distance (from the table) for the ultrasonic sensor
    
            \"\"\"
            Behavior.__init__(self)
            self.supressed = False
            self.back_ult = back_ult
            self.motor = motor
            self.leds = leds
            self.sound = sound
            self.heigth_treshold = heigth_treshold        

            self.back_cliff = False
            self.operations = []


        
        def check(self):
            \"\"\"
            Check if the ultrasonic sensor detect a cliff
            @return: True if the ultrasonic sensor detect a cliff
            @rtype: bool
            \"\"\"
            back_sensor = read_ultrasonic_sensor(self.back_ult)
            back_cliff = back_sensor \> self.heigth_treshold and back_sensor \< 2550  # when the sensor is too close to the ground it returns 2550

            if back_cliff != self.back_cliff:
                self.back_cliff = back_cliff
                if back_cliff:
                    self.operations = self._get_operations(back_cliff)
                    return True

            return False
        

        def _get_operations(self, back):
            if back: # back cliff behind the robot
                return [lambda: self.motor.turn(degrees=5), lambda: self.motor.run(forward=True, speedM=0.5, distance=5)]

            if DEBUG:
                timedlog(\"Back sensors: \" + str(back))

            return []
        
        def _reset(self):
            self.back_cliff = False
            self.motor.stop()


        def action(self):
            \"\"\"
            Change direction to step away from the border
            \"\"\"

            # operations = self._get_operations(self.edge[\"left\"], self.edge[\"mid\"], self.edge[\"right\"], self.back_cliff)
            self.supressed = False
            if DEBUG:
                timedlog(\"Cliff avoidance \" + str(self.back_cliff))

            for operation in self.operations:
                operation()
                while self.motor.is_running and not self.supressed:
                    pass
                if self.supressed:
                    break
            
            self._reset()
            if DEBUG and not self.supressed:
                timedlog(\"Cliff avoidance done\")
            return not self.supressed


        def suppress(self):
            \"\"\"
            Suppress the behavior
            \"\"\"
            self.motor.stop()
            self.supressed = True
            if DEBUG:
                timedlog(\"Cliff avoidance suppressed\")


    class EdgeAvoidanceBhv(Behavior):
        \"\"\"
        This behavior will check if the robot is on the black border, and tries to step away from it
        \"\"\"

        def __init__(self, left_cs, mid_cs, right_cs, motor, leds=False, sound=False, edge_color=\"white\"):
            \"\"\"
            Initialize the behavior
            @param left_cs: The left color sensor to use
            @param mid_cs: The middle color sensor to use
            @param right_cs: The right color sensor to use
            @param back_ult: The back ultrasonic sensor to use
            @param motor: the motor to use
            @param leds: the leds to use
            @param sound: the sound to use
            @param heigth_treshold: The treshold distance (from the table) for the ultrasonic sensor
    
            \"\"\"
            Behavior.__init__(self)
            self.supressed = False
            self.left_cs = left_cs
            self.mid_cs = mid_cs
            self.right_cs = right_cs
            self.motor = motor
            self.leds = leds
            self.sound = sound

            self.edge = {\"left\": False, \"mid\": False, \"right\": False}
            self.left_c, self.mid_c, self.right_c = \"black\", \"black\", \"black\"
            self.edge_color = edge_color
            self.operations = []


        
        def check(self):
            \"\"\"
            Check if the color sensor is on a white surface
            @return: True if the color sensor is on a white surface
            @rtype: bool
            \"\"\"
            self.left_c, self.mid_c, self.right_c = read_color_sensor(self.left_cs), read_color_sensor(self.mid_cs), read_color_sensor(self.right_cs)

            left_edge = self.left_c == self.edge_color
            mid_edge = self.mid_c == self.edge_color 
            right_edge = self.right_c == self.edge_color 

            if left_edge != self.edge[\"left\"] or mid_edge != self.edge[\"mid\"] or right_edge != self.edge[\"right\"]:
                self.edge[\"left\"] = left_edge
                self.edge[\"mid\"] = mid_edge
                self.edge[\"right\"] = right_edge

                
                if any([left_edge, mid_edge, right_edge]):
                    self.operations = self._get_operations(left_edge, mid_edge, right_edge)
                    return True

            return False
        

        def _get_operations(self, left, mid, right):
            
            if all([left, mid, right]):  # all sensors on the edge
                return [lambda: self.motor.run(forward=False, distance=10), lambda: self.motor.turn(degrees=60)]
            
            if all([left, right]):  # left and right sensors on the edge
                return [lambda: self.motor.run(forward=False, distance=5), lambda: self.motor.turn(degrees=60)]
            
            if all([left, mid]):  # left and mid sensors on the edge
                return [lambda: self.motor.run(forward=False, distance=8), lambda: self.motor.turn(direction=RIGHT, degrees=30)]
            
            if all([mid, right]):  # mid and right sensors on the edge
                return [lambda: self.motor.run(forward=False, distance=8), lambda: self.motor.turn(direction=LEFT, degrees=30)]

            if left:  # left sensor on the edge
                if self.right_c == \"black\":
                    return [lambda: self.motor.run(forward=False, distance=5), lambda: self.motor.turn(direction=RIGHT, degrees=30)]
                else:
                    return [lambda: self.motor.run(forward=True, speedM=0.5, distance=3), lambda: self.motor.turn(direction=RIGHT, degrees=20), lambda: self.motor.run(forward=False, distance=5)]

            if right:  # right sensor on the edge
                if self.left_c == \"black\":
                    return [lambda: self.motor.run(forward=False, distance=5), lambda: self.motor.turn(direction=LEFT, degrees=30)]
                else:
                    return [lambda: self.motor.run(forward=True, speedM=0.5, distance=3), lambda: self.motor.turn(direction=LEFT, degrees=20), lambda: self.motor.run(forward=False, distance=5)]
            
            if mid: # mid sensor on the edge
                direction = RIGHT if self.right_c == \"black\" else LEFT
                return [lambda: self.motor.run(forward=False, distance=3), lambda: self.motor.turn(direction=direction, degrees=15)]


            if DEBUG:
                timedlog(\"Edge sensors: \" + str(left) + \" \" + str(mid) + \" \" + str(right))

            return []

        def _reset(self):
            self.edge = {\"left\": False, \"mid\": False, \"right\": False}
            self.motor.stop()


        def action(self):
            \"\"\"
            Change direction to step away from the border
            \"\"\"

            # operations = self._get_operations(self.edge[\"left\"], self.edge[\"mid\"], self.edge[\"right\"], self.back_cliff)
            self.supressed = False
            if DEBUG:
                timedlog(\"Edge collision \" + str(self.edge))
            avoid_stuck = [lambda: self.motor.run(forward=False, distance=20), lambda: self.motor.turn(degrees=5)] if random.random() \< 0.2 else []
            for operation in avoid_stuck + self.operations:
                operation()
                while self.motor.is_running and not self.supressed:
                    pass
                if self.supressed:
                    break
            
            self._reset()
            if DEBUG and not self.supressed:
                timedlog(\"Edge collision done\")
            return not self.supressed



        def suppress(self):
            \"\"\"
            Suppress the behavior
            \"\"\"
            self.motor.stop()
            self.supressed = True
            if DEBUG:
                timedlog(\"Edge collision suppressed\")

    class LakeAvoidanceBhv(Behavior):
        \"\"\"
        This behavior will check if the robot is on a lake, and tries to step away from it
        \"\"\"

        def __init__(self, left_cs, mid_cs, right_cs, motor, leds=False, sound=False, lake_colors=[\"yellow\", \"blue\", \"red\", \"brown\"]):
            \"\"\"
            Initialize the behavior
            @param left_cs: The left color sensor to use
            @param mid_cs: The middle color sensor to use
            @param right_cs: The right color sensor to use
            @param motor: the motor to use
            @param leds: the leds to use
            @param sound: the sound to use
            @param heigth_treshold: The treshold distance (from the table) for the ultrasonic sensor
    
            \"\"\"
            Behavior.__init__(self)
            self.supressed = False
            self.left_cs = left_cs
            self.mid_cs = mid_cs
            self.right_cs = right_cs
            self.motor = motor
            self.leds = leds
            self.sound = sound

            self.edge = {\"left\": False, \"mid\": False, \"right\": False, \"mid_nc\": False}
            self.lake_colors = lake_colors
            self.operations = []


        
        def check(self):
            \"\"\"
            Check if the color sensor is on a black surface
            @return: True if the color sensor is on a black surface
            @rtype: bool
            \"\"\"
            mid_color = read_color_sensor(self.mid_cs)

            left_edge = read_color_sensor(self.left_cs) in self.lake_colors  # note maybe we should check against the table color instead of the edge color
            mid_edge = mid_color in self.lake_colors
            right_edge = read_color_sensor(self.right_cs) in self.lake_colors
            mid_nc = mid_color == \"nocolor\"

            if left_edge != self.edge[\"left\"] or mid_edge != self.edge[\"mid\"] or right_edge != self.edge[\"right\"] or mid_nc != self.edge[\"mid_nc\"]:
                self.edge[\"left\"] = left_edge
                self.edge[\"mid\"] = mid_edge
                self.edge[\"right\"] = right_edge
                self.edge[\"mid_nc\"] = mid_nc
                
                if any([left_edge, mid_edge, right_edge, mid_nc]):
                    self.operations = self._get_operations(left_edge, mid_edge, right_edge, mid_nc)
                    return True

            return False
        

        def _get_operations(self, left, mid, right, mid_nc):
            
            if all([left, mid]):  # left and mid sensors on the edge
                return [lambda: self.motor.turn(direction=LEFT, degrees=40)]

        
            if all([mid, right]):  # mid and right sensors on the edge
                return [lambda: self.motor.turn(direction=RIGHT, degrees=40)]

            
            if left:  # left sensor on the edge
                return [lambda: self.motor.turn(direction=RIGHT, degrees=15)]

            if right:  # right sensor on the edge
                return [lambda: self.motor.turn(direction=LEFT, degrees=15)]
            
            
            if mid:  # left sensor on the edge
                return [lambda: self.motor.run(forward=False, distance=10), lambda: self.motor.turn(degrees=45)]
            
            if mid_nc:  # mid sensor on the void (caused by some movements)
                return [lambda: self.motor.run(forward=False, distance=10), lambda: self.motor.turn(degrees=45)]

            if DEBUG:
                timedlog(\"Lake sensors: \" + str(left) + \" \" + str(mid) + \" \" + str(right) + \" \")

            return []

        def _reset(self):
            self.edge = {\"left\": False, \"mid\": False, \"right\": False, \"mid_nc\": False}
            self.motor.stop()


        def action(self):
            \"\"\"
            Change direction to step away from the border
            \"\"\"

            # operations = self._get_operations(self.edge[\"left\"], self.edge[\"mid\"], self.edge[\"right\"])
            self.supressed = False
            if DEBUG:
                timedlog(\"Lake collision\")

            avoid_stuck = [lambda: self.motor.run(forward=False, distance=10), lambda: self.motor.turn(degrees=5)] if random.random() \< 0.2 else []
            for operation in avoid_stuck + self.operations:
                operation()
                while self.motor.is_running and not self.supressed:
                    pass
                if self.supressed:
                    break
            
            self._reset()
            if DEBUG and not self.supressed:
                timedlog(\"Lake collision done\")
            return not self.supressed


        def suppress(self):
            \"\"\"
            Suppress the behavior
            \"\"\"
            self.motor.stop()
            self.supressed = True
            if DEBUG:
                timedlog(\"Lake collision suppressed\")

    class UpdateSlaveReadings(Behavior):
        \"\"\"
        This simple behavior, at each check cycle, will update the slave readings without doing anything else
        \"\"\"
            
    
        def __init__(self, bluetooth_connection, readings_dict):
            \"\"\"
            Initialize the behavior
            @param bluetooth_connection: The bluetooth connection to useù
            @param readings_dict: The readings dictionary to update
            
            \"\"\"
            Behavior.__init__(self)
            self.bluetooth_connection = bluetooth_connection
            self.readings_dict = readings_dict
            self.data = \"\"

            self.direction = None

        
        def check(self):
            \"\"\"
            Check if the bluetooth connection has recived a new reading
            @return: True if the bluetooth connection has recived a new reading
            @rtype: bool
            \"\"\"

            data = self.bluetooth_connection.get_data()
            if data != \"\":
                self.data = data
                self._update_readings_dict()
            
            return False
        
        def _update_readings_dict(self):
            data = self.data.split(\",\")
            self.readings_dict[\"touch_left\"] = bool(int(data[0]))
            self.readings_dict[\"touch_right\"] = bool(int(data[1]))
            self.readings_dict[\"touch_back\"] = bool(int(data[2]))
            self.readings_dict[\"ult_front\"] = int(data[3])

            # log = \"Readings: \" + str(self.readings_dict[\'touch_left\']) + \",\" + str(self.readings_dict[\'touch_right\']) + \",\" + str(self.readings_dict[\'touch_back\']) + \",\" + str(self.readings_dict[\'ult_front\'])
            # timedlog(log)
                
        def action(self):
            \"\"\"
            Do nothing
            \"\"\"
            return True



        def suppress(self):
            \"\"\"
            Suppress the behavior
            \"\"\"
            pass




    class AvoidCollisionBhv(Behavior):
        \"\"\"
        This behavior will check if the front ultrasonic sensor dedect an object, and makes the robot avoid it
        \"\"\"
            
        def __init__(self, readings_dict, motor, leds=False, sound=False, threshold_distance=300):
            \"\"\"
            Initialize the behavior
            @param readings_dict: The readings dictionary to use for the ultrasonic front and touch back
            @param motor: the motor to use
            @param leds: the leds to use
            @param sound: the sound to use

            \"\"\"
            Behavior.__init__(self)
            self.supressed = False
            self.motor = motor
            self.leds = leds
            self.sound = sound
            self.threshold_distance = threshold_distance        

            self.readings_dict = readings_dict
            self.obj_front = False
            self.operations = []

        
        def check(self):
            \"\"\"
            Check if the ultrasonic sensor dedect an object
            @return: True if the ultrasonic sensor dedect an object
            @rtype: bool
            \"\"\"
            
            obj_front = self.readings_dict[\"ult_front\"] \< self.threshold_distance

            if obj_front != self.obj_front:
                self.obj_front = obj_front

                if obj_front:
                    self.operations = self._get_operations(obj_front)
                    return True
            return False
            
        def _reset(self):
            self.obj_front = False
        
        def _get_operations(self, obj_front):
            if obj_front:
                return [lambda: self.motor.turn(degrees=45)]
                
            
        def action(self):
            \"\"\"
            Change direction to step away from the object
            \"\"\"

            self.suppressed = False
            if DEBUG:
                timedlog(\"Collision avoidance\")
            
            for operation in self.operations:
                operation()
                while self.motor.is_running and not self.supressed:
                    pass
                if self.supressed:
                    break
            
            self._reset()
            return not self.suppressed


        def suppress(self):
            \"\"\"
            Suppress the behavior
            \"\"\"
            self.motor.stop()
            self.suppressed = True
            if DEBUG:
                timedlog(\"Collision avoidance suppressed\")



    class RecoverCollisionBhv(Behavior):
        \"\"\"
        This behavior will check if we had collide with something, and makes the robot recover from it
        \"\"\"
            
        def __init__(self, readings_dict, motor, leds=False, sound=False):
            \"\"\"
            Initialize the behavior
            @param readings_dict: The readings dictionary to use for the touch sensors left and right and touch back
            @param motor: the motor to use
            @param leds: the leds to use
            @param sound: the sound to use

            \"\"\"
            Behavior.__init__(self)
            self.supressed = False
            self.motor = motor
            self.leds = leds
            self.sound = sound       

            self.readings_dict = readings_dict
            self.operations = []


            self.obj_left = False
            self.obj_right = False
            self.obj_back = False

        
        def check(self):
            \"\"\"
            Check if the ultrasonic sensor dedect an object
            @return: True if the ultrasonic sensor dedect an object
            @rtype: bool
            \"\"\"
            
            obj_left = self.readings_dict[\"touch_left\"]
            obj_right = self.readings_dict[\"touch_right\"]
            obj_back = self.readings_dict[\"touch_back\"]


            if obj_left != self.obj_left or obj_right != self.obj_right or obj_back != self.obj_back:
                self.obj_left = obj_left
                self.obj_right = obj_right
                self.obj_back = obj_back
                
                if any([obj_left, obj_right, obj_back]):
                    self.operations = self._get_operations(obj_left, obj_right, obj_back)
                    return True

            return False
        
        def _reset(self):
            self.obj_left = False
            self.obj_right = False
            self.obj_back = False

        def _get_operations(self, obj_left, obj_right, obj_back):
            # if all([obj_left, obj_right, obj_back]): # stuck position
                # return []
            if all([obj_left, obj_right]): # left and right sensors touched
                return [lambda: self.motor.run(forward=False, distance=10), lambda: self.motor.turn(degrees=40)]
            if obj_left: # left sensor touched
                return [lambda: self.motor.run(forward=False, distance=5), lambda: self.motor.turn(direction=RIGHT, degrees=40)]
            if obj_right: # right sensor touched
                return [lambda: self.motor.run(forward=False, distance=5), lambda: self.motor.turn(direction=LEFT, degrees=40)]
            if obj_back: # back sensor touched
                return [lambda: self.motor.run(forward=True, distance=5)]
            
                

        def action(self):
            \"\"\"
            Change direction to step away from the object
            \"\"\"

            self.suppressed = False
            if DEBUG:
                timedlog(\"Collision recover\")
            
            for operation in self.operations:
                operation()
                while self.motor.is_running and not self.supressed:
                    pass
                if self.supressed:
                    break
            
            self._reset()
            return not self.suppressed

        def suppress(self):
            \"\"\"
            Suppress the behavior
            \"\"\"
            self.motor.stop()
            self.suppressed = True
            if DEBUG:
                timedlog(\"Collision recover suppressed\")

    CS_L, CS_M, CS_R, US_B, M_L, M_R, M_A, LEFT, RIGHT = INPUT_1, INPUT_2, INPUT_3, INPUT_4, OUTPUT_A, OUTPUT_B, OUTPUT_C, -1, 1

    CS_L, CS_M, CS_R, US_B, move_differential, arm_steering, LEDS, S = ColorSensor(CS_L), ColorSensor(CS_M), ColorSensor(CS_R), UltrasonicSensor(US_B), MoveDifferential(M_L, M_R, wheel_class=EV3EducationSetTire, wheel_distance_mm=123), MediumMotor(M_A), Leds(), Sound()

    US_B.mode = \'US-DIST-CM\'
    MOTOR = Motor(move_differential)
    ARM = ArmMotor(arm_steering)

    CONTROLLER = Controller(return_when_no_action=True)


    master_mac = \'78:DB:2F:2B:5D:98\'
    master = True

    BLUETOOTH_CONNECTION = BluetoothConnection(master, master_mac, debug=DEBUG)
    READINGS_DICT = {\"touch_left\": False, \"touch_right\": False, \"touch_back\": False, \"ult_front\": 1000}

    # task_registry = TaskRegistry()

    s.speak(\'Start\')
    if DEBUG:
        timedlog(\"Starting\")





    CONTROLLER.add(UpdateSlaveReadings(BLUETOOTH_CONNECTION, READINGS_DICT))
    CONTROLLER.add(CliffAvoidanceBhv(US_B, MOTOR))
    CONTROLLER.add(EdgeAvoidanceBhv(CS_L, CS_M, CS_R, MOTOR))
    CONTROLLER.add(LakeAvoidanceBhv(CS_L, CS_M, CS_R, MOTOR))
    CONTROLLER.add(RecoverCollisionBhv(READINGS_DICT, MOTOR))
    CONTROLLER.add(AvoidCollisionBhv(READINGS_DICT, MOTOR))
    CONTROLLER.add(RunningBhv(MOTOR, LEDS))





    BLUETOOTH_CONNECTION.start_listening(lambda data: ())
    controller.start()

    S.speak(\"stop\")
                '";

    master_bhvs = "
    'CONTROLLER.add(UpdateSlaveReadings(BLUETOOTH_CONNECTION, READINGS_DICT))
    'CONTROLLER.add(CliffAvoidanceBhv(US_B, MOTOR))
    'CONTROLLER.add(EdgeAvoidanceBhv(CS_L, CS_M, CS_R, MOTOR))
    'CONTROLLER.add(LakeAvoidanceBhv(CS_L, CS_M, CS_R, MOTOR))
    'CONTROLLER.add(RecoverCollisionBhv(READINGS_DICT, MOTOR))
    'CONTROLLER.add(AvoidCollisionBhv(READINGS_DICT, MOTOR))
    'CONTROLLER.add(RunningBhv(MOTOR, LEDS))
    '";

    return <rVal, master_bhvs>;
}