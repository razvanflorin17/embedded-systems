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

DEBUG = False
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
        
        if random_rep and bhv is not None and  random.random() < 0.2:
            self.turn(degrees=40, speed=speed, speedM=speedM, block=block, brake=brake)
            while self.is_running and not bhv.suppressed:
                pass

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


def set_global_MEASURE_OBJ(value):
    global MEASURE_OBJ
    MEASURE_OBJ = value

def set_global_OVERRIDED_LAKE(value):
    global OVERRIDED_LAKE
    OVERRIDED_LAKE = value

def set_global_MEASURE_LAKE(value):
    global MEASURE_LAKE
    MEASURE_LAKE = value

MASTER = False
MASTER_MAC = "00:17:E9:B2:1E:41"
#!/usr/bin/env python3

import random

from ev3dev2.motor import SpeedPercent, MoveSteering, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.display import Display
from ev3dev2.sound import Sound
from ev3dev2.led import Leds
from ev3dev2.sensor.lego import ColorSensor, TouchSensor, UltrasonicSensor
from ev3dev2._platform.ev3 import INPUT_1, INPUT_2, INPUT_3, INPUT_4
import bluetooth, threading

if DEBUG:
    from ev3devlogging import timedlog

TS_L, TS_R, TS_B, US_F, LEFT, RIGHT = INPUT_1, INPUT_2, INPUT_3, INPUT_4, -1, 1

TS_L, TS_R, TS_B, US_F, S = TouchSensor(TS_L), TouchSensor(TS_R), TouchSensor(TS_B), UltrasonicSensor(US_F), Sound()
US_F.mode = 'US-DIST-CM'


BLUETOOTH_CONNECTION = BluetoothConnection(MASTER, MASTER_MAC, debug=DEBUG)
READINGS_DICT = {"TS_L": False, "TS_R": False, "TS_B": False, "US_F": 0}



#!/usr/bin/env python3

import random

from ev3dev2.motor import SpeedPercent, MoveSteering, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.display import Display
from ev3dev2.sound import Sound
from ev3dev2.led import Leds
from ev3dev2.sensor.lego import ColorSensor, TouchSensor, UltrasonicSensor
from ev3dev2._platform.ev3 import INPUT_1, INPUT_2, INPUT_3, INPUT_4
from ev3devlogging import timedlog

import bluetooth, threading
import time



class UpdateSlaveReadingsBhv(Behavior):
    """
    This behavior will check if the robot touch an object, and tries to step away from it
    """
    
    def __init__(self):
        """
        Initialize the behavior
        @param touch_left: The left touch sensor to use
        @param touch_right: The right touch sensor to use
        @param touch_back: The back touch sensor to use
        @param ult_front: The front ultrasonic sensor to use
        @param bluetooth_connection: The bluetooth connection to use
        @param readings_dict: The readings dictionary to update and send
        
        """
        Behavior.__init__(self)

        self.direction = None

    
    def check(self):
        """
        Check if the touch sensor is pressed
        @return: True if the touch sensor is pressed
        @rtype: bool
        """
        return True
        

    def action(self):
        """
        Update the dictionary with the new readings and send them to the master
        """

        READINGS_DICT["TS_L"] = read_touch_sensor(TL)
        READINGS_DICT["TS_R"] = read_touch_sensor(TR)
        READINGS_DICT["TS_B"] = read_touch_sensor(TB)
        READINGS_DICT["US_F"] = read_ultrasonic_sensor(US_F)

        msg = str(READINGS_DICT['TS_L']) + "," + str(READINGS_DICT['TS_R']) + "," + str(READINGS_DICT['TS_B']) + "," + str(READINGS_DICT['US_F'])
        log = "Sending Readings: " + msg
        if DEBUG:
            timedlog(log)
        BLUETOOTH_CONNECTION.write(msg)
        
        time.sleep(0.05)

        return True


    def suppress(self):
        """
        Suppress the behavior
        """
        pass

CONTROLLER = Controller(return_when_no_action=True)
CONTROLLER.add(UpdateSlaveReadingsBhv())
if DEBUG:
	timedlog("Starting")
CONTROLLER.start()