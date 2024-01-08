#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading


class Behavior(object):
    """
    This is an abstract class. Should embody an specific behavior belonging to a robot. Each Behavior must define three
    things and should be implemented by the user:
    1. check: Under what circumcises should this behavior take control.
    2. action: What should this behavior do while it has control.
    3. suppress: Should give up control immediately when this method is called. Will be called when a behavior with a
    higher priority wants to take control.
    """

    def check(self):
        """
        Method to check whether if this behavior should be started or not.
        @return: Should return a true value if this behavior should take control or not
        """
        raise NotImplementedError("Should have implemented this")

    def action(self):
        """
        The code in action should represent what the behavior should do while it's active. When this method returns
        the action is complete and the robot should be in a complete safe state, ie the motors are shut down and such,
        so the next behavior can take safely take control of the robot
        """
        raise NotImplementedError("Should have implemented this")

    def suppress(self):
        """
        Should immediately cause the behavior to exits it execution and put the state in safe mode. In other words it
        should cause the action() method to stop it's execution
        """
        raise NotImplementedError("Should have implemented this")


class Controller():
    """
    Runs the main subsumption logic. Controls which behavior will run based on their priority and if they want to become
    active or not. Works as a scheduler, where only one behavior can be active at a time and who is active is decided by
    the sensor data and their priority. The previous active behavior gets suppressed when a behavior with a higher
    priority wants to run.

    There is two usages in this class. One is to make the class take care of scheduler itself, by calling the start()
    method. The other is to take care of the scheduler by yourself, by using the step() method
    """

    def __init__(self, return_when_no_action):
        """
        Initialize the object. Notice the subsumption module is not bound to a specific brick, the behaviors are. This
        makes it possible to have a subsumption module responsible for multiple bricks at the same time, if desirable.
        """
        self.behaviors = []
        self.wait_object = threading.Event()
        self.active_behavior_index = None

        self._running = True
        self._return_when_no_action = return_when_no_action

        self.callback = lambda x: 0

    def add(self, behavior):
        """
        Add a behavior to the behavior module. The order decide which priority they have. First > Second
        @type behavior: Behavior
        """
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
        """
        Find the next active behavior and runs it.
        @return: Returns whether it got to run any behavior or not
        """
        behavior = self.find_next_active_behavior()
        if behavior is not None:
            self.behaviors[behavior].action()
            return True
        return False

    def find_next_active_behavior(self):
        """
        Finds the next behavior that wants to run, if any
        @return: Next runnable behavior if any
        @rtype: int
        """
        for priority, behavior in enumerate(self.behaviors):
            if behavior.check():
                return priority
        return None

    def _find_and_set_new_active_behavior(self):
        new_behavior_priority = self.find_next_active_behavior()
        if self.active_behavior_index is None or (new_behavior_priority is not None and self.active_behavior_index > new_behavior_priority):
            if self.active_behavior_index is not None:
                self.behaviors[self.active_behavior_index].suppress()
            self.active_behavior_index = new_behavior_priority

            # Callback to tell something it changed the active behavior if anything is interested
            self.callback(self.active_behavior_index)

    def _start(self):  # run the action methods
        """
        Starts finding and running behaviors, suppressing the old behaviors when new behaviors with higher priority
        wants to run.
        """
        self._running = True
        self._find_and_set_new_active_behavior()  # force do it ourselves once to find the right one
        thread = threading.Thread(name="Continuous behavior checker",
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
            thread = threading.Thread(name="Subsumption Thread",
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

#!/usr/bin/env python3

DEBUG = True
if DEBUG:
    from ev3devlogging import timedlog
import random
from ev3dev2.motor import SpeedPercent
from ev3dev2.sound import Sound
import bluetooth, threading, time


SOUND_NO_BLOCK = Sound.PLAY_NO_WAIT_FOR_COMPLETE # sound option that doesn't block the program
BASE_SPEED = 20
LEFT, RIGHT = -1, 1
BLACK = 1

def int2color(colornr):
    color_dict = {0: "nocolor", 1: "black", 2: "blue", 3: "green", 4: "yellow", 5: "red", 6: "white", 7: "yellow"} # 7 should be brown
    return color_dict[colornr]


def set_leds_color(leds, color):
    if color not in ["BLACK", "RED", "GREEN", "AMBER", "ORANGE", "YELLOW"]:
       color = "AMBER"
    leds.set_color("LEFT", color) 
    leds.set_color("RIGHT", color)

def feedback_leds_blocking(leds, color): # for generated code
    set_leds_color(leds, color)
    time.sleep(0.5)
    leds.reset()


class ArmMotor():
    """
    Wrapper class for the motor, all beahviors should use this class to control the motor.
    In the future if we want to change the type of motor, we only have to change this class
    """
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
    """
    Wrapper class for the differential motor, all beahviors should use this class to control the motor.
    In the future if we want to change the type of motor, we only have to change this class
    """
    def __init__(self, motor, base_speed=BASE_SPEED):
        self.motor = motor
        self.base_speed = base_speed
        # self.log_distance = 0
        # self.log_angle = 0

    def run(self, forward=True, distance=10, speed=None, speedM=None, block=False, brake=False):
        """Runs the motor for a certain distance (cm)"""
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
    
    def to_coordinates(self, x, y, speed=None, speedM=0.5, block=False, brake=False, random_rep=False, bhv=None):
        if speed is None:
            speed = self.base_speed * speedM
        
        if random_rep and bhv is not None and random.random() < 0.2:
            for operation in [lambda: self.turn(degrees=40, speed=speed, speedM=speedM, block=block, brake=brake), lambda: self.run(distance=50, speed=speed, speedM=speedM, block=block, brake=brake)]:
                operation()
                while self.is_running and not bhv.suppressed:
                    pass
                if bhv.suppressed:
                    break

            if not bhv.suppressed:
                self.motor.on_to_coordinates(SpeedPercent(speed), x*10, y*10, block=block, brake=brake) # x and y are in mm
        else:
            self.motor.on_to_coordinates(SpeedPercent(speed), x*10, y*10, block=block, brake=brake) # x and y are in mm

    # def log_reset(self):
    #     self.log_distance = 0
    #     self.log_angle = 0
    
    # def log_distance(self, distance):
    #     self.log_distance += distance
    
    # def log_angle(self, angle):
    #     self.log_angle += angle
    
    # def get_log_distance(self):
    #     return self.log_distance
    
    # def get_log_angle(self):
    #     return self.log_angle

    @property
    def is_running(self):
        return self.motor.is_running
        
# class Motor():
#     """
#     Wrapper class for the steering motor, all beahviors should use this class to control the motor.
#     In the future if we want to change the type of motor, we only have to change this class
#     """
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
    """
    Class to keep track of tasks that have to be done before the robot can stop.

    Before starting the robot, the main program should add all the tasks that have to be done, 
    so the RunningBhv will check the registry to see if all tasks are done, and if so, stop the robot.
    """
    def __init__(self):
        self.tasks = {}

    def add(self, task_name, n_trigger=1):
        self.tasks[task_name] = [False] * n_trigger

    def set(self, task_name, value, trigger_index=0):
        self.tasks[task_name][trigger_index] = value
    
    def set_all(self, task_name, value):
        self.tasks[task_name] = [value] * len(self.tasks[task_name])

    def update(self, task_name, value, trigger_index=0):
        self.tasks[task_name][trigger_index] = max(self.tasks[task_name][trigger_index], value)

    def get(self, task_name, trigger_index=0):
        return self.tasks[task_name][trigger_index] if trigger_index is not None else self.tasks[task_name]
    
    def task_done(self, task_name):
        return all(self.tasks[task_name])

    def all_tasks_done(self):
        return all([self.task_done(task_name) for task_name in self.tasks])
    
    def reset(self):
        self.tasks = {}


class BluetoothConnection():
    """
    Class to handle the bluetooth connection between the master and the slave.
    """
    def __init__(self, is_master, server_mac, port=3, debug=False):
        """
        Initializes the socks for the connection.
        @param is_master: True if this brick is the master, False if it's the slave
        @param server_mac: The mac address of the master brick
        @param port: The port to use for the connection
        @param debug: Whether to print debug messages or not
        """

        self.is_master = is_master
        self.server_mac = server_mac
        self.port = port
        self.debug = debug
        self.buffer = [""] # buffer for the data that is received
        
        self.startup()

    def startup(self):
        """
        Starts the connection between the master and the slave.
        """
        if self.is_master:
            self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_sock.bind((self.server_mac, self.port))
            self.server_sock.listen(20)
            
            if self.debug:
                timedlog('Listening for connections from the slave...')

            client_sock, address = self.server_sock.accept()
            if self.debug:
                timedlog('Accepted connection')
            self.client_sock = client_sock

        else:
            time.sleep(6)
            self.client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            if self.debug:
                timedlog("Connecting to the master...")

            self.client_sock.connect((self.server_mac, self.port))

            
            if self.debug:
                timedlog("Connected to the master")
        
        self.sock_in = self.client_sock.makefile('r')
        self.sock_out = self.client_sock.makefile('w')
        
    def write(self, data):
        """
        Sends data to the other brick.
        @param data: The data to send
        """
        self.sock_out.write(str(data) + "\n")
        self.sock_out.flush()

    def _read(self):
        """
        Reads data from the other brick.
        @return: The data that was readq
        """
        data = str(self.sock_in.readline())
        
        return data.replace("\n", "")
    
    def _listen(self, procedure):
        """
        Listens for data from the other brick.
        @param procedure: The procedure to call when data is received (that take the data as argument)
        """
        while True:
            data = self._read()
            self.buffer[0] = str(data)
            procedure(data)
    
    def start_listening(self, procedure):
        """
        Starts listening for data from the other brick, by opening a thread.
        @param procedure: The procedure to call when data is received (that take the data as argument)
        """

        listener = threading.Thread(target=self._listen, args=[procedure])
        listener.start()

    def get_data(self):
        """
        Gets the data that was received from the other brick.
        @return: The data that was received
        """
        return self.buffer[0]

    def shutdown(self):
        """
        Closes the connection between the master and the slave.
        """
        self.sock_in.close()
        self.sock_out.close()
        self.client_sock.close()
        if self.is_master:
            self.server_sock.close()


def set_color_ranges(color_dict, ranges, color_name):
    for r_range, g_range, b_range in ranges:
        for red in range(r_range[0], r_range[1] + 1):
            for green in range(g_range[0], g_range[1] + 1):
                for blue in range(b_range[0], b_range[1] + 1):
                    color_dict[(red, green, blue)] = color_name


def read_color_sensor(cs):  
    """
    Reads the color sensor and returns the color that was read.
    @param color_sensor: The color sensor to read
    @return: The color that was read
    """
    lock = threading.Lock()

    with lock:
        try:
            color = cs.color
        except: 
            if DEBUG:
                timedlog("Color sensor wrong read")
            return read_color_sensor(cs)
        return int2color(color)

def read_ultrasonic_sensor(ultrasonic_sensor):
    """
    Reads the ultrasonic sensor and returns the distance.
    @param color_sensor: The ultrasonic sensor to read
    @return: The distance that was read
    """
    lock = threading.Lock()
    
    with lock:
        try:
            distance = ultrasonic_sensor.value()
        except: 
            if DEBUG:
                timedlog("Ultrasonic sensor wrong read")
            return read_ultrasonic_sensor(ultrasonic_sensor)
        return distance

def read_touch_sensor(touch_sensor):
    """
    Reads the touch sensor and returns the distance.
    @param color_sensor: The touch sensor to read
    @return: The touch that was read
    """
    lock = threading.Lock()
    
    with lock:
        try:
            touch = touch_sensor.is_pressed
        except: 
            if DEBUG:
                timedlog("Touch sensor wrong read")
            return read_touch_sensor(touch_sensor)
        return touch


import random

from ev3dev2.motor import MoveDifferential, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.wheel import EV3EducationSetTire
from ev3dev2.sound import Sound
from ev3dev2.led import Leds
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor
from ev3dev2._platform.ev3 import INPUT_1, INPUT_2, INPUT_3, INPUT_4
if DEBUG:
    from ev3devlogging import timedlog



CS_L, CS_M, CS_R, US_B, M_L, M_R, M_A, LEFT, RIGHT = INPUT_1, INPUT_2, INPUT_3, INPUT_4, OUTPUT_A, OUTPUT_B, OUTPUT_C, -1, 1

CS_L, CS_M, CS_R, US_B, move_differential, arm_steering, LEDS, S = ColorSensor(CS_L), ColorSensor(CS_M), ColorSensor(CS_R), UltrasonicSensor(US_B), MoveDifferential(M_L, M_R, wheel_class=EV3EducationSetTire, wheel_distance_mm=123), MediumMotor(M_A), Leds(), Sound()

US_B.mode = 'US-DIST-CM'
MOTOR = Motor(move_differential)
ARM = ArmMotor(arm_steering)

READINGS_DICT = {"TS_L": False, "TS_R": False, "TS_B": False, "US_F": 1000, "US_B": 1000, "CS_R": None, "CS_M": None, "CS_L": None}
TASK_REGISTRY = TaskRegistry()
TASK_REGISTRY.add("RunningBhv")

class RunningBhv(Behavior):

    def __init__(self):
        Behavior.__init__(self)
        self.suppressed = False

    def check(self):

        return not TASK_REGISTRY.all_tasks_done()

    def action(self):
        """
        Keep the robot moving
        """

        self.suppressed = False
        if DEBUG:
            timedlog("Moving")
        
        # while not self.suppressed:
        #     MOTOR.run(forward=True, distance=10, brake=False)
        #     while MOTOR.is_running and not self.suppressed:
        #         pass
        #     if not self.suppressed:
        #         MOTOR.apply_momentum()

        MOTOR.run(forward=True, distance=1000, brake=False, speedM=1.3)
        while MOTOR.is_running and not self.suppressed:
            pass

        return not self.suppressed


    def suppress(self):
        """
        Suppress the behavior
        """
        MOTOR.stop()
        self.suppressed = True
        if DEBUG:
            timedlog("Moving suppressed")


class CliffAvoidanceBhv(Behavior):
    """
    This behavior will check if the robot is on falling off the cliff
    """

    def __init__(self, heigth_treshold_min=120, heigth_treshold_max=400):
        Behavior.__init__(self)
        self.suppressed = False
        self.heigth_treshold_min = heigth_treshold_min
        self.heigth_treshold_max = heigth_treshold_max   

        self.back_cliff = False
        self.operations = []


    
    def check(self):
        """
        Check if the ultrasonic sensor detect a cliff
        @return: True if the ultrasonic sensor detect a cliff
        @rtype: bool
        """

        back_sensor = READINGS_DICT["US_B"]
        back_cliff = back_sensor > self.heigth_treshold_min and back_sensor < self.heigth_treshold_max

        if back_cliff != self.back_cliff:
            self.back_cliff = back_cliff
            if back_cliff:
                self.operations = self._get_operations(back_cliff)
                return True

        return False
    

    def _get_operations(self, back):
        if back: # back cliff behind the robot
            return [lambda: MOTOR.turn(degrees=5), lambda: MOTOR.run(forward=True, speedM=0.5, distance=3)]

        return []
    
    def _reset(self):
        self.back_cliff = False
        MOTOR.stop()


    def action(self):
        """
        Change direction to step away from the border
        """

        self.fire = True
        self.suppressed = False
        if DEBUG:
            timedlog("Cliff avoidance " + str(self.back_cliff))

        for operation in self.operations:
            operation()
            while MOTOR.is_running and not self.suppressed:
                pass
            if self.suppressed:
                break
        
        self._reset()
        if DEBUG and not self.suppressed:
            timedlog("Cliff avoidance done")
        return not self.suppressed


    def suppress(self):
        """
        Suppress the behavior
        """
        MOTOR.stop()
        self.suppressed = True
        if DEBUG:
            timedlog("Cliff avoidance suppressed")


class EdgeAvoidanceBhv(Behavior):
    """
    This behavior will check if the robot is on the black border, and tries to step away from it
    """

    def __init__(self, edge_color="white"):
        """
        Initialize the behavior
        @param heigth_treshold: The treshold distance (from the table) for the ultrasonic sensor
 
        """
        Behavior.__init__(self)
        self.suppressed = False

        self.edge = {"left": False, "mid": False, "right": False}
        self.left_c, self.mid_c, self.right_c = "black", "black", "black"
        self.edge_color = edge_color
        self.operations = []


    
    def check(self):
        """
        Check if the color sensor is on a white surface
        @return: True if the color sensor is on a white surface
        @rtype: bool
        """

        self.left_c, self.mid_c, self.right_c = READINGS_DICT["CS_L"], READINGS_DICT["CS_M"], READINGS_DICT["CS_R"]

        left_edge = self.left_c == self.edge_color
        mid_edge = self.mid_c == self.edge_color 
        right_edge = self.right_c == self.edge_color 

        if left_edge != self.edge["left"] or mid_edge != self.edge["mid"] or right_edge != self.edge["right"]:
            self.edge["left"] = left_edge
            self.edge["mid"] = mid_edge
            self.edge["right"] = right_edge

            
            if any([left_edge, mid_edge, right_edge]):
                self.operations = self._get_operations(left_edge, mid_edge, right_edge)
                return True

        return False
    

    def _get_operations(self, left, mid, right):
        
        if all([left, mid, right]):  # all sensors on the edge
            return [lambda: MOTOR.run(forward=False, distance=4), lambda: MOTOR.turn(degrees=60)]
        
        if all([left, right]):  # left and right sensors on the edge
            return [lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(degrees=60)]
        
        if all([left, mid]):  # left and mid sensors on the edge
            return [lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(direction=RIGHT, degrees=30)]
        
        if all([mid, right]):  # mid and right sensors on the edge
            return [lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(direction=LEFT, degrees=30)]

        if left:  # left sensor on the edge
            if self.right_c == "black":
                return [lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(direction=RIGHT, degrees=30)]
            else:
                return [lambda: MOTOR.run(forward=True, speedM=0.5, distance=3), lambda: MOTOR.turn(direction=RIGHT, degrees=20), lambda: MOTOR.run(forward=False, distance=5)]

        if right:  # right sensor on the edge
            if self.left_c == "black":
                return [lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(direction=LEFT, degrees=30)]
            else:
                return [lambda: MOTOR.run(forward=True, speedM=0.5, distance=3), lambda: MOTOR.turn(direction=LEFT, degrees=20), lambda: MOTOR.run(forward=False, distance=5)]
        
        if mid: # mid sensor on the edge
            direction = RIGHT if self.right_c == "black" else LEFT
            return [lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(direction=direction, degrees=30)]

        return []

    def _reset(self):
        self.edge = {"left": False, "mid": False, "right": False}
        MOTOR.stop()


    def action(self):
        """
        Change direction to step away from the border
        """
        self.suppressed = False
        if DEBUG:
            timedlog("Edge collision " + str(self.edge))
        avoid_stuck = [lambda: MOTOR.run(forward=False, distance=10), lambda: MOTOR.turn(degrees=5)] if random.random() < 0.1 else []
        for operation in avoid_stuck + self.operations:
            operation()
            while MOTOR.is_running and not self.suppressed:
                pass
            if self.suppressed:
                break
        
        self._reset()
        if DEBUG and not self.suppressed:
            timedlog("Edge collision done")
        return not self.suppressed



    def suppress(self):
        """
        Suppress the behavior
        """
        MOTOR.stop()
        self.suppressed = True
        if DEBUG:
            timedlog("Edge collision suppressed")

class LakeAvoidanceBhv(Behavior):
    """
    This behavior will check if the robot is on a lake, and tries to step away from it
    """

    def __init__(self, lake_colors=["yellow", "blue", "red"]):
        """
        Initialize the behavior
        @param left_cs: The left color sensor to use
        @param mid_cs: The middle color sensor to use
        @param right_cs: The right color sensor to use
        @param motor: the motor to use
        @param leds: the leds to use
        @param sound: the sound to use
        @param heigth_treshold: The treshold distance (from the table) for the ultrasonic sensor
 
        """
        Behavior.__init__(self)
        self.suppressed = False
        # self.measure = measure
        # self.last_color = None

        self.edge = {"left": False, "mid": False, "right": False, "mid_nc": False}
        self.lake_colors = lake_colors
        self.detected_colors = {color: False for color in self.lake_colors}
        self.operations = []


    
    def check(self):
        """
        Check if the color sensor is on a black surface
        @return: True if the color sensor is on a black surface
        @rtype: bool
        """

        
        mid_color = READINGS_DICT["CS_M"]
        left_color = READINGS_DICT["CS_L"]
        right_color = READINGS_DICT["CS_R"]

        left_edge = left_color in self.lake_colors  # note maybe we should check against the table color instead of the edge color
        mid_edge = mid_color in self.lake_colors
        right_edge = right_color in self.lake_colors
        mid_nc = mid_color == "nocolor"

        if left_edge != self.edge["left"] or mid_edge != self.edge["mid"] or right_edge != self.edge["right"] or mid_nc != self.edge["mid_nc"]:
            self.edge["left"] = left_edge
            self.edge["mid"] = mid_edge
            self.edge["right"] = right_edge
            self.edge["mid_nc"] = mid_nc
            
            if any([left_edge, mid_edge, right_edge]):
                
                # if self.measure:
                #     timedlog(self.detected_colors)
                #     color = next((color for color in [left_color, mid_color, right_color] if color in self.lake_colors), None)
                #     if color is not None:
                #         if self.detected_colors[color]:
                #             self.operations = self._get_operations(left_edge, mid_edge, right_edge, mid_nc)
                #         else:
                #             self.last_color = next((c for c in self.lake_colors if not self.detected_colors[c]), None)
                #             timedlog("LAST COLOR -----------------------")
                #             timedlog(self.last_color)
                #             self.operations = self._get_operations_measure(left_edge, mid_edge, right_edge, mid_nc)
                #     else:
                #         self.operations = self._get_operations(left_edge, mid_edge, right_edge, mid_nc)
                # else:
                #     self.operations = self._get_operations(left_edge, mid_edge, right_edge, mid_nc)
                self.operations = self._get_operations(left_edge, mid_edge, right_edge, mid_nc)
                
                return True

        return False
    

    # def _get_operations_measure(self, left, mid, right, mid_nc):
    #     if all([left, mid]):
    #         return [lambda: MOTOR.turn(direction=LEFT, degrees=5), 
    #                 lambda: self.arm_motor.move(up=False, block=True), lambda: self.arm_motor.move(block=True),
    #                 lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(direction=LEFT, degrees=40)]
        
    #     if all([mid, right]):
    #         return [lambda: MOTOR.turn(direction=RIGHT, degrees=5), 
    #                 lambda: self.arm_motor.move(up=False, block=True), lambda: self.arm_motor.move(block=True),
    #                 lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(direction=RIGHT, degrees=40)]
        
    #     if left:
    #         return [lambda: MOTOR.turn(direction=LEFT, degrees=15), 
    #                 lambda: self.arm_motor.move(up=False, block=True), lambda: self.arm_motor.move(block=True),
    #                 lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(direction=LEFT, degrees=20)]

    #     if right:
    #         return [lambda: MOTOR.turn(direction=RIGHT, degrees=15), 
    #                 lambda: self.arm_motor.move(up=False, block=True), lambda: self.arm_motor.move(block=True),
    #                 lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(direction=RIGHT, degrees=20)]
                        
    #     if mid:
    #         return [lambda: self.arm_motor.move(up=False, block=True), lambda: self.arm_motor.move(block=True),
    #                 lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(degrees=40)]

    #     return []


    def _get_operations(self, left, mid, right, mid_nc):
        
        if all([left, mid]):  # left and mid sensors on the edge
            return [lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(direction=LEFT, degrees=40)]

    
        if all([mid, right]):  # mid and right sensors on the edge
            return [lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(direction=RIGHT, degrees=40)]

        
        if left:  # left sensor on the edge
            return [lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(direction=RIGHT, degrees=20)]

        if right:  # right sensor on the edge
            return [lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(direction=LEFT, degrees=20)]
        
        
        if mid:  # left sensor on the edge
            return [lambda: MOTOR.run(forward=False, distance=3), lambda: MOTOR.turn(degrees=40)]
        
        if mid_nc:  # mid sensor on the void (caused by some movements)
            return [lambda: MOTOR.run(forward=False, distance=5), lambda: MOTOR.turn(degrees=40)]

        if DEBUG:
            timedlog("Lake sensors: " + str(left) + " " + str(mid) + " " + str(right) + " ")

        return []

    def _reset(self):
        self.edge = {"left": False, "mid": False, "right": False, "mid_nc": False}
        MOTOR.stop()


    def action(self):
        """
        Change direction to step away from the border
        """

        self.suppressed = False
        if DEBUG:
            timedlog("Lake collision  " + str(self.edge))

        avoid_stuck = [lambda: MOTOR.run(forward=False, distance=10), lambda: MOTOR.turn(degrees=5)] if random.random() < 0.1 else []
        for operation in avoid_stuck + self.operations:
            operation()
            while MOTOR.is_running and not self.suppressed:
                pass
            # if self.last_color is not None:
            #     self.detected_colors[self.last_color] = True
            #     self.last_color = None
            if self.suppressed:
                break
        
        self._reset()
        if DEBUG and not self.suppressed:
            timedlog("Lake collision done")
        return not self.suppressed


    def suppress(self):
        """
        Suppress the behavior
        """
        MOTOR.stop()
        self.suppressed = True
        if DEBUG:
            timedlog("Lake collision suppressed")

class UpdateSlaveReadings(Behavior):
    """
    This simple behavior, at each check cycle, will update the slave readings without doing anything else
    """
        
   
    def __init__(self):
        Behavior.__init__(self)

        self.data = ""

        self.direction = None

    
    def check(self):
        """
        Check if the bluetooth connection has recived a new reading
        @return: True if the bluetooth connection has recived a new reading
        @rtype: bool
        """

        data = BLUETOOTH_CONNECTION.get_data()
        if data != "":
            self.data = data
            self._update_readings_dict()
        
        return False
    
    def _update_readings_dict(self):
        data = self.data.split(",")
        READINGS_DICT["touch_left"] = bool(int(data[0]))
        READINGS_DICT["touch_right"] = bool(int(data[1]))
        READINGS_DICT["touch_back"] = bool(int(data[2]))
        READINGS_DICT["ult_front"] = int(data[3])
        

        if DEBUG:
            timedlog("Readings: " + str(READINGS_DICT))

        # log = "Readings: " + str(READINGS_DICT['touch_left']) + "," + str(READINGS_DICT['touch_right']) + "," + str(READINGS_DICT['touch_back']) + "," + str(READINGS_DICT['ult_front'])
        # timedlog(log)
            
    def action(self):
        """
        Do nothing
        """
        return True



    def suppress(self):
        """
        Suppress the behavior
        """
        pass


class UpdateReadings(Behavior):
    """
    This simple behavior, at each check cycle, will update the slave readings without doing anything else
    """
        
   
    def __init__(self):
        """
        Initialize the behavior
        @param BLUETOOTH_CONNECTION: The bluetooth connection to useù
        @param readings_dict: The readings dictionary to update
        
        """
        Behavior.__init__(self)
        self.data = ""
    
    def check(self):
        """
        Check if the bluetooth connection has recived a new reading
        @return: True if the bluetooth connection has recived a new reading
        @rtype: bool
        """

        # data = self.BLUETOOTH_CONNECTION.get_data()
        # if data != "":
        #     self.data = data
        #     self._update_readings_dict()

        self._update_readings_dict()
        
        return False
    
    def _update_readings_dict(self):
        # data = self.data.split(",")
        # READINGS_DICT["TS_L"] = bool(int(data[0]))
        # READINGS_DICT["TS_R"] = bool(int(data[1]))
        # READINGS_DICT["TS_B"] = bool(int(data[2]))
        # READINGS_DICT["US_F"] = int(data[3])

        READINGS_DICT["CS_L"] = read_color_sensor(CS_L)
        READINGS_DICT["CS_M"] = read_color_sensor(CS_M)
        READINGS_DICT["CS_R"] = read_color_sensor(CS_R)
        READINGS_DICT["US_B"] = read_ultrasonic_sensor(US_B)
        
        # timedlog("Readings: " + str(READINGS_DICT))
        # log = "Readings: " + str(READINGS_DICT['touch_left']) + "," + str(READINGS_DICT['touch_right']) + "," + str(READINGS_DICT['touch_back']) + "," + str(READINGS_DICT['ult_front'])
        # timedlog(log)
            
    def action(self):
        """
        Do nothing
        """
        return True



    def suppress(self):
        """
        Suppress the behavior
        """
        pass




class AvoidCollisionBhv(Behavior):
    """
    This behavior will check if the front ultrasonic sensor dedect an object, and makes the robot avoid it
    """
        
    def __init__(self, threshold_distance=300):
        """
        Initialize the behavior
        @param readings_dict: The readings dictionary to use for the ultrasonic front and touch back
        @param motor: the motor to use
        @param leds: the leds to use
        @param sound: the sound to use

        """
        Behavior.__init__(self)
        self.suppressed = False
        self.threshold_distance = threshold_distance        
        self.obj_front = False
        self.operations = []

    
    def check(self):
        """
        Check if the ultrasonic sensor dedect an object
        @return: True if the ultrasonic sensor dedect an object
        @rtype: bool
        """
        
        
        obj_front = READINGS_DICT["ult_front"] < self.threshold_distance

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
            return [lambda: MOTOR.turn(degrees=45)]
            
        
    def action(self):
        """
        Change direction to step away from the object
        """

        self.suppressed = False
        if DEBUG:
            timedlog("Collision avoidance")
        
        for operation in self.operations:
            operation()
            while MOTOR.is_running and not self.suppressed:
                pass
            if self.suppressed:
                break
        
        self._reset()
        return not self.suppressed


    def suppress(self):
        """
        Suppress the behavior
        """
        MOTOR.stop()
        self.suppressed = True
        if DEBUG:
            timedlog("Collision avoidance suppressed")



class RecoverCollisionBhv(Behavior):
    """
    This behavior will check if we had collide with something, and makes the robot recover from it
    """
        
    def __init__(self):

        Behavior.__init__(self)
        self.suppressed = False
        self.operations = []
        self.obj_left = False
        self.obj_right = False
        self.obj_back = False

    
    def check(self):
        """
        Check if the ultrasonic sensor dedect an object
        @return: True if the ultrasonic sensor dedect an object
        @rtype: bool
        """
        
        obj_left = READINGS_DICT["touch_left"]
        obj_right = READINGS_DICT["touch_right"]
        obj_back = READINGS_DICT["touch_back"]


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
            return [lambda: MOTOR.run(forward=False, distance=10), lambda: MOTOR.turn(degrees=40)]
        if obj_left: # left sensor touched
            return [lambda: MOTOR.run(forward=False, distance=5), lambda: MOTOR.turn(direction=RIGHT, degrees=40)]
        if obj_right: # right sensor touched
            return [lambda: MOTOR.run(forward=False, distance=5), lambda: MOTOR.turn(direction=LEFT, degrees=40)]
        if obj_back: # back sensor touched
            return [lambda: MOTOR.run(forward=True, distance=5)]
        
            

    def action(self):
        """
        Change direction to step away from the object
        """

        self.suppressed = False
        if DEBUG:
            timedlog("Collision recover")
        
        for operation in self.operations:
            operation()
            while MOTOR.is_running and not self.suppressed:
                pass
            if self.suppressed:
                break
         
        self._reset()
        return not self.suppressed

    def suppress(self):
        """
        Suppress the behavior
        """
        MOTOR.stop()
        self.suppressed = True
        if DEBUG:
            timedlog("Collision recover suppressed")

"211"




class bb_bhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.suppressed = False
		self.operations = []
		self.counter_conds = 0
		self.trigger_list = [lambda: READINGS_DICT["TS_L"], lambda: READINGS_DICT["CS_M"] == "black", lambda: READINGS_DICT["ULT_B"] < 10, lambda: READINGS_DICT["CS_L"] == "black"]
		self.firing = False
		self.to_fire = False


	def _reset(self):
		self.operations = []
		MOTOR.stop()
		self.counter_conds = 0
		self.trigger_list = [lambda: READINGS_DICT["TS_L"], lambda: READINGS_DICT["CS_M"] == "black", lambda: READINGS_DICT["ULT_B"] < 10, lambda: READINGS_DICT["CS_L"] == "black"]
		self.firing = False
		self.to_fire = False


	def check(self):
		if not self.to_fire and not self.firing:
			if self.trigger_list[self.counter_conds]():
				self.counter_conds += 1
				self.to_fire = (self.counter_conds == 4)
		
			if self.to_fire:
				self.operations = [lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: S.beep()]
		return self.to_fire and not self.firing



	def action(self):
		global OVERRIDED_LAKE, MEASURE_OBJ
		self.suppressed = False
		self.firing = True
		self.to_fire = False
		if DEBUG:
			timedlog("bb fired")

		for operation in self.operations:
			operation()
			while MOTOR.is_running and not self.suppressed:
				pass
			if self.suppressed:
				break

		self._reset()

		if DEBUG and not self.suppressed:
			timedlog("bb done")
		return not self.suppressed


	def suppress(self):
		MOTOR.stop()
		self.suppressed = True
		if DEBUG:
			timedlog("bb suppressed")




class bc_bhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.suppressed = False
		self.operations = []
		self.firing = False
		self.to_fire = False


	def _reset(self):
		self.operations = []
		MOTOR.stop()
		self.firing = False
		self.to_fire = False


	def check(self):
		if not self.to_fire and not self.firing:
			self.to_fire = (READINGS_DICT["CS_M"] == "black" or READINGS_DICT["CS_L"] == "black" or READINGS_DICT["ULT_B"] < 10)
		
			if self.to_fire:
				self.operations = [lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: S.beep(), lambda: MOTOR.turn(direction="RIGHT", degrees=90, speed=30)]
		return self.to_fire and not self.firing



	def action(self):
		global OVERRIDED_LAKE, MEASURE_OBJ
		self.suppressed = False
		self.firing = True
		self.to_fire = False
		if DEBUG:
			timedlog("bc fired")

		for operation in self.operations:
			operation()
			while MOTOR.is_running and not self.suppressed:
				pass
			if self.suppressed:
				break

		self._reset()

		if DEBUG and not self.suppressed:
			timedlog("bc done")
		return not self.suppressed


	def suppress(self):
		MOTOR.stop()
		self.suppressed = True
		if DEBUG:
			timedlog("bc suppressed")




class bd_bhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.suppressed = False
		self.operations = []
		self.firing = False
		self.to_fire = False


	def _reset(self):
		self.operations = []
		MOTOR.stop()
		self.firing = False
		self.to_fire = False


	def check(self):
		if not self.to_fire and not self.firing:
			self.to_fire = (READINGS_DICT["CS_M"] == "black" and READINGS_DICT["CS_L"] == "black" and READINGS_DICT["ULT_B"] < 10)
		
			if self.to_fire:
				self.operations = [lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: S.beep(), lambda: MOTOR.turn(direction="RIGHT", degrees=90, speed=30), lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: (MEASURE_OBJ := True), lambda: ARM.move(up=False, rotations=0.5, block=True), lambda: time.sleep(36000), lambda: ARM.move(up=True, rotations=0.5, block=True), lambda: (MEASURE_OBJ := False), lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: S.beep(), lambda: MOTOR.turn(direction="RIGHT", degrees=90, speed=30)]
		return self.to_fire and not self.firing



	def action(self):
		global OVERRIDED_LAKE, MEASURE_OBJ
		self.suppressed = False
		self.firing = True
		self.to_fire = False
		if DEBUG:
			timedlog("bd fired")

		for operation in self.operations:
			operation()
			while MOTOR.is_running and not self.suppressed:
				pass
			if self.suppressed:
				break

		self._reset()

		if DEBUG and not self.suppressed:
			timedlog("bd done")
		return not self.suppressed


	def suppress(self):
		MOTOR.stop()
		self.suppressed = True
		if DEBUG:
			timedlog("bd suppressed")




class ba_bhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.suppressed = False
		self.operations = []
		self.firing = False
		self.to_fire = False


	def _reset(self):
		self.operations = []
		MOTOR.stop()
		self.firing = False
		self.to_fire = False


	def check(self):
		if not self.to_fire and not self.firing:
			self.to_fire = (READINGS_DICT["CS_M"] == "black")
		
			if self.to_fire:
				self.operations = [lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: MOTOR.run(forward=True, distance=10, speed=30), lambda: MOTOR.run(forward=True, distance=10, speed=30)]
		return self.to_fire and not self.firing



	def action(self):
		global OVERRIDED_LAKE, MEASURE_OBJ
		self.suppressed = False
		self.firing = True
		self.to_fire = False
		if DEBUG:
			timedlog("ba fired")

		for operation in self.operations:
			operation()
			while MOTOR.is_running and not self.suppressed:
				pass
			if self.suppressed:
				break

		self._reset()

		if DEBUG and not self.suppressed:
			timedlog("ba done")
		return not self.suppressed


	def suppress(self):
		MOTOR.stop()
		self.suppressed = True
		if DEBUG:
			timedlog("ba suppressed")




class ma_controllerBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.executing_state = 0
		self.counter_action = 0
		self.running_actions_done = False
		self.fired = False
		self.timer = 0
		self.timeouted = False
		TASK_REGISTRY.add("state_0", 1)
		TASK_REGISTRY.add("state_1", 1)
		TASK_REGISTRY.add("state_2", 1)
		TASK_REGISTRY.add("state_3", 1)
		self.task_list_cond = [[lambda: self.running_actions_done], [lambda: READINGS_DICT["CS_M"] == "black" or READINGS_DICT["CS_L"] == "black" or READINGS_DICT["TS_L"] or READINGS_DICT["ULT_B"] < 10], [lambda: self.running_actions_done], [lambda: READINGS_DICT["CS_M"] == "black"]]
		self.timeout = [60, 30, 180, 60]
		self.operations = [[lambda: (MEASURE_OBJ := True), lambda: ARM.move(up=False, rotations=0.5, block=True), lambda: time.sleep(36000), lambda: ARM.move(up=True, rotations=0.5, block=True), lambda: (MEASURE_OBJ := False)], [lambda: MOTOR.run(forward=True, distance=100, brake=False, speedM=1.3), lambda: self._caction_dec()], [lambda: MOTOR.odometry_start(), lambda: MOTOR.to_coordinates(0, 10, speed=30, random_rep=True, bhv=self), lambda: MOTOR.to_coordinates(10, 20, speed=30, random_rep=True, bhv=self), lambda: MOTOR.to_coordinates(31, 41, speed=10, random_rep=True, bhv=self), lambda: MOTOR.odometry_stop()], [lambda: MOTOR.run(forward=True, distance=100, brake=False, speedM=1.3), lambda: self._caction_dec()]]

	def check(self):
		if self.timeouted:
			return True
		if TASK_REGISTRY.all_tasks_done():
			return False

		if self.timer == 0:
			self.timer = time.time()
		else:
			self.timeouted = (time.time() - self.timer) > self.timeout[self.executing_state]
			if self.timeouted:
				self.suppress()
				TASK_REGISTRY.set_all("state_" + str(self.executing_state), 1)
				self.executing_state += 1
				self.running_actions_done = False
				self.timer = 0
				return True


		for i in range(len(self.task_list_cond[self.executing_state])):
			TASK_REGISTRY.update("state_" + str(self.executing_state), self.task_list_cond[self.executing_state][i](), i)
		
		if TASK_REGISTRY.task_done("state_" + str(self.executing_state)):
			self.suppress()
			self.executing_state += 1
			self.counter_action = 0
			self.running_actions_done = False
			self.timer = 0
			return self.executing_state < 4

		return not self.fired

	def action(self):
		global OVERRIDED_LAKE, MEASURE_OBJ, MEASURE_LAKE
		if self.timeouted:
			MOTOR.stop()
			if DEBUG:
				timedlog("ma timeouted, at state" + str(self.executing_state - 1))
			for operation in [lambda: S.speak("Mission ma timeouted")]:
				operation()
			self.timeouted = False
			return True

		self.suppressed = False
		self.fired = True
		for operation in self.operations[self.executing_state][self.counter_action:]:
			operation()
			while MOTOR.is_running and not self.suppressed and not TASK_REGISTRY.task_done("state_" + str(self.executing_state)):
				pass
			if self.suppressed:
				break
			else:
				self.counter_action += 1
		
		if not self.suppressed and self.counter_action == len(self.operations[self.executing_state]):
			self.running_actions_done = True
			self.counter_action = 0

		self.fired = False
		return not self.suppressed

	def _caction_dec(self, cond=True):
		if cond:
			self.counter_action = self.counter_action - 2

	def suppress(self):
		MOTOR.stop()
		self.suppressed = True
		if DEBUG:
			timedlog("RunningBhv suppressed")




class mb_controllerBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.executing_state = 0
		self.counter_action = 0
		self.running_actions_done = False
		self.fired = False
		self.timer = 0
		self.timeouted = False
		TASK_REGISTRY.add("state_0", 1)
		self.task_list_cond = [[lambda: self.running_actions_done]]
		self.timeout = [60]
		self.operations = [[lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE), lambda: S.speak("Hello World", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE)]]

	def check(self):
		if self.timeouted:
			return True
		if TASK_REGISTRY.all_tasks_done():
			return False

		if self.timer == 0:
			self.timer = time.time()
		else:
			self.timeouted = (time.time() - self.timer) > self.timeout[self.executing_state]
			if self.timeouted:
				self.suppress()
				TASK_REGISTRY.set_all("state_" + str(self.executing_state), 1)
				self.executing_state += 1
				self.running_actions_done = False
				self.timer = 0
				return True


		for i in range(len(self.task_list_cond[self.executing_state])):
			TASK_REGISTRY.update("state_" + str(self.executing_state), self.task_list_cond[self.executing_state][i](), i)
		
		if TASK_REGISTRY.task_done("state_" + str(self.executing_state)):
			self.suppress()
			self.executing_state += 1
			self.counter_action = 0
			self.running_actions_done = False
			self.timer = 0
			return self.executing_state < 1

		return not self.fired

	def action(self):
		global OVERRIDED_LAKE, MEASURE_OBJ, MEASURE_LAKE
		if self.timeouted:
			MOTOR.stop()
			if DEBUG:
				timedlog("mb timeouted, at state" + str(self.executing_state - 1))
			for operation in [lambda: S.beep(), lambda: S.beep()]:
				operation()
			self.timeouted = False
			return True

		self.suppressed = False
		self.fired = True
		for operation in self.operations[self.executing_state][self.counter_action:]:
			operation()
			while MOTOR.is_running and not self.suppressed and not TASK_REGISTRY.task_done("state_" + str(self.executing_state)):
				pass
			if self.suppressed:
				break
			else:
				self.counter_action += 1
		
		if not self.suppressed and self.counter_action == len(self.operations[self.executing_state]):
			self.running_actions_done = True
			self.counter_action = 0

		self.fired = False
		return not self.suppressed

	def _caction_dec(self, cond=True):
		if cond:
			self.counter_action = self.counter_action - 2

	def suppress(self):
		MOTOR.stop()
		self.suppressed = True
		if DEBUG:
			timedlog("RunningBhv suppressed")




class md_controllerBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.executing_state = 0
		self.counter_action = 0
		self.running_actions_done = False
		self.fired = False
		self.timer = 0
		self.timeouted = False
		TASK_REGISTRY.add("state_0", 1)
		TASK_REGISTRY.add("state_1", 1)
		self.task_list_cond = [[lambda: READINGS_DICT["CS_M"] == "black"], [lambda: READINGS_DICT["CS_L"] == "black"]]
		self.timeout = [60, 60]
		self.operations = [[lambda: MOTOR.run(forward=True, distance=100, brake=False, speedM=1.3), lambda: self._caction_dec()], [lambda: MOTOR.run(forward=True, distance=100, brake=False, speedM=1.3), lambda: self._caction_dec()]]

	def check(self):
		if self.timeouted:
			return True
		if TASK_REGISTRY.all_tasks_done():
			return False

		if self.timer == 0:
			self.timer = time.time()
		else:
			self.timeouted = (time.time() - self.timer) > self.timeout[self.executing_state]
			if self.timeouted:
				self.suppress()
				TASK_REGISTRY.set_all("state_" + str(self.executing_state), 1)
				self.executing_state += 1
				self.running_actions_done = False
				self.timer = 0
				return True


		for i in range(len(self.task_list_cond[self.executing_state])):
			TASK_REGISTRY.update("state_" + str(self.executing_state), self.task_list_cond[self.executing_state][i](), i)
		
		if TASK_REGISTRY.task_done("state_" + str(self.executing_state)):
			self.suppress()
			self.executing_state += 1
			self.counter_action = 0
			self.running_actions_done = False
			self.timer = 0
			return self.executing_state < 2

		return not self.fired

	def action(self):
		global OVERRIDED_LAKE, MEASURE_OBJ, MEASURE_LAKE
		if self.timeouted:
			MOTOR.stop()
			if DEBUG:
				timedlog("md timeouted, at state" + str(self.executing_state - 1))
			for operation in [lambda: S.speak("Mission md timeouted")]:
				operation()
			self.timeouted = False
			return True

		self.suppressed = False
		self.fired = True
		for operation in self.operations[self.executing_state][self.counter_action:]:
			operation()
			while MOTOR.is_running and not self.suppressed and not TASK_REGISTRY.task_done("state_" + str(self.executing_state)):
				pass
			if self.suppressed:
				break
			else:
				self.counter_action += 1
		
		if not self.suppressed and self.counter_action == len(self.operations[self.executing_state]):
			self.running_actions_done = True
			self.counter_action = 0

		self.fired = False
		return not self.suppressed

	def _caction_dec(self, cond=True):
		if cond:
			self.counter_action = self.counter_action - 2

	def suppress(self):
		MOTOR.stop()
		self.suppressed = True
		if DEBUG:
			timedlog("RunningBhv suppressed")




class mf_controllerBhv(Behavior):
	def __init__(self):
		Behavior.__init__(self)
		self.executing_state = 0
		self.counter_action = 0
		self.running_actions_done = False
		self.fired = False
		self.timer = 0
		self.timeouted = False
		TASK_REGISTRY.add("state_0", 1)
		self.task_list_cond = [[lambda: READINGS_DICT["CS_M"] == "black"]]
		self.timeout = [60]
		self.operations = [[lambda: MOTOR.run(forward=True, distance=100, brake=False, speedM=1.3), lambda: self._caction_dec()]]

	def check(self):
		if self.timeouted:
			return True
		if TASK_REGISTRY.all_tasks_done():
			return False

		if self.timer == 0:
			self.timer = time.time()
		else:
			self.timeouted = (time.time() - self.timer) > self.timeout[self.executing_state]
			if self.timeouted:
				self.suppress()
				TASK_REGISTRY.set_all("state_" + str(self.executing_state), 1)
				self.executing_state += 1
				self.running_actions_done = False
				self.timer = 0
				return True


		for i in range(len(self.task_list_cond[self.executing_state])):
			TASK_REGISTRY.update("state_" + str(self.executing_state), self.task_list_cond[self.executing_state][i](), i)
		
		if TASK_REGISTRY.task_done("state_" + str(self.executing_state)):
			self.suppress()
			self.executing_state += 1
			self.counter_action = 0
			self.running_actions_done = False
			self.timer = 0
			return self.executing_state < 1

		return not self.fired

	def action(self):
		global OVERRIDED_LAKE, MEASURE_OBJ, MEASURE_LAKE
		if self.timeouted:
			MOTOR.stop()
			if DEBUG:
				timedlog("mf timeouted, at state" + str(self.executing_state - 1))
			for operation in [lambda: S.beep()]:
				operation()
			self.timeouted = False
			return True

		self.suppressed = False
		self.fired = True
		for operation in self.operations[self.executing_state][self.counter_action:]:
			operation()
			while MOTOR.is_running and not self.suppressed and not TASK_REGISTRY.task_done("state_" + str(self.executing_state)):
				pass
			if self.suppressed:
				break
			else:
				self.counter_action += 1
		
		if not self.suppressed and self.counter_action == len(self.operations[self.executing_state]):
			self.running_actions_done = True
			self.counter_action = 0

		self.fired = False
		return not self.suppressed

	def _caction_dec(self, cond=True):
		if cond:
			self.counter_action = self.counter_action - 2

	def suppress(self):
		MOTOR.stop()
		self.suppressed = True
		if DEBUG:
			timedlog("RunningBhv suppressed")




CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()


CONTROLLER.add(UpdateReadings())
CONTROLLER.add(CliffAvoidanceBhv())
CONTROLLER.add(EdgeAvoidanceBhv())
CONTROLLER.add(LakeAvoidanceBhv())
CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
CONTROLLER.add(bc_bhv())
CONTROLLER.add(bd_bhv())
# CONTROLLER.add(RecoverCollisionBhv(readings_dict, motor))
# controller.add(AvoidCollisionBhv(readings_dict, motor))

CONTROLLER.add(ma_controllerBhv())
#BLUETOOTH_CONNECTION.start_listening(lambda data: ())
S.speak('Start') # REMOVE BEFORE DELIVERY

for operation in [lambda: S.speak("Starting mission ma")]:
	operation()

if DEBUG:
	timedlog("Starting ma")
CONTROLLER.start()


for operation in [lambda: S.speak("Mission ma done")]:
	operation()

if DEBUG:
	timedlog("Done ma")





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()


CONTROLLER.add(UpdateReadings())
CONTROLLER.add(CliffAvoidanceBhv())
CONTROLLER.add(EdgeAvoidanceBhv())
CONTROLLER.add(LakeAvoidanceBhv())
CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
# CONTROLLER.add(RecoverCollisionBhv(readings_dict, motor))
# controller.add(AvoidCollisionBhv(readings_dict, motor))

CONTROLLER.add(mb_controllerBhv())
#BLUETOOTH_CONNECTION.start_listening(lambda data: ())
S.speak('Start') # REMOVE BEFORE DELIVERY

for operation in [lambda: S.speak("Hello World", play_type=S.PLAY_WAIT_FOR_COMPLETE), lambda: S.beep()]:
	operation()

if DEBUG:
	timedlog("Starting mb")
CONTROLLER.start()


for operation in [lambda: S.beep(), lambda: S.beep(), lambda: feedback_leds_blocking(LEDS, "GREEN")]:
	operation()

if DEBUG:
	timedlog("Done mb")





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()


CONTROLLER.add(UpdateReadings())
CONTROLLER.add(CliffAvoidanceBhv())
CONTROLLER.add(EdgeAvoidanceBhv())
CONTROLLER.add(LakeAvoidanceBhv())
CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
CONTROLLER.add(bc_bhv())
CONTROLLER.add(bd_bhv())
# CONTROLLER.add(RecoverCollisionBhv(readings_dict, motor))
# controller.add(AvoidCollisionBhv(readings_dict, motor))

CONTROLLER.add(ma_controllerBhv())
#BLUETOOTH_CONNECTION.start_listening(lambda data: ())
S.speak('Start') # REMOVE BEFORE DELIVERY

for operation in [lambda: S.speak("Starting mission ma")]:
	operation()

if DEBUG:
	timedlog("Starting ma")
CONTROLLER.start()


for operation in [lambda: S.speak("Mission ma done")]:
	operation()

if DEBUG:
	timedlog("Done ma")





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()


CONTROLLER.add(UpdateReadings())
CONTROLLER.add(CliffAvoidanceBhv())
CONTROLLER.add(EdgeAvoidanceBhv())
CONTROLLER.add(LakeAvoidanceBhv())
CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
# CONTROLLER.add(RecoverCollisionBhv(readings_dict, motor))
# controller.add(AvoidCollisionBhv(readings_dict, motor))

CONTROLLER.add(mb_controllerBhv())
#BLUETOOTH_CONNECTION.start_listening(lambda data: ())
S.speak('Start') # REMOVE BEFORE DELIVERY

for operation in [lambda: S.speak("Hello World", play_type=S.PLAY_WAIT_FOR_COMPLETE), lambda: S.beep()]:
	operation()

if DEBUG:
	timedlog("Starting mb")
CONTROLLER.start()


for operation in [lambda: S.beep(), lambda: S.beep(), lambda: feedback_leds_blocking(LEDS, "GREEN")]:
	operation()

if DEBUG:
	timedlog("Done mb")





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()


CONTROLLER.add(UpdateReadings())
CONTROLLER.add(CliffAvoidanceBhv())
CONTROLLER.add(EdgeAvoidanceBhv())
CONTROLLER.add(LakeAvoidanceBhv())
CONTROLLER.add(ba_bhv())
CONTROLLER.add(bb_bhv())
CONTROLLER.add(bd_bhv())
CONTROLLER.add(bc_bhv())
# CONTROLLER.add(RecoverCollisionBhv(readings_dict, motor))
# controller.add(AvoidCollisionBhv(readings_dict, motor))

CONTROLLER.add(md_controllerBhv())
#BLUETOOTH_CONNECTION.start_listening(lambda data: ())
S.speak('Start') # REMOVE BEFORE DELIVERY

for operation in [lambda: S.speak("Starting mission md")]:
	operation()

if DEBUG:
	timedlog("Starting md")
CONTROLLER.start()


for operation in [lambda: S.speak("Mission md done")]:
	operation()

if DEBUG:
	timedlog("Done md")





CONTROLLER = Controller(return_when_no_action=True)
TASK_REGISTRY = TaskRegistry()


CONTROLLER.add(UpdateReadings())
CONTROLLER.add(CliffAvoidanceBhv())
CONTROLLER.add(EdgeAvoidanceBhv())
CONTROLLER.add(LakeAvoidanceBhv())
CONTROLLER.add(ba_bhv())
# CONTROLLER.add(RecoverCollisionBhv(readings_dict, motor))
# controller.add(AvoidCollisionBhv(readings_dict, motor))

CONTROLLER.add(mf_controllerBhv())
#BLUETOOTH_CONNECTION.start_listening(lambda data: ())
S.speak('Start') # REMOVE BEFORE DELIVERY

for operation in [lambda: S.beep()]:
	operation()

if DEBUG:
	timedlog("Starting mf")
CONTROLLER.start()


for operation in [lambda: S.speak("Mission mf done")]:
	operation()

if DEBUG:
	timedlog("Done mf")





