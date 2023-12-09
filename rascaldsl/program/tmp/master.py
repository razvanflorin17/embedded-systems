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


##########################################################################
##########################################################################
#########################                #################################
#########################  SUBS_ARCH.PY  #################################
#########################                #################################
##########################################################################
##########################################################################


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
        if self.active_behavior_index is None or self.active_behavior_index > new_behavior_priority:
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
    

##########################################################################
##########################################################################
#########################              ###################################
#########################  COMMONS.PY  ###################################
#########################              ###################################
##########################################################################
##########################################################################


SOUND_NO_BLOCK = Sound.PLAY_NO_WAIT_FOR_COMPLETE # sound option that doesn't block the program
BASE_SPEED = 25
LEFT, RIGHT = -1, 1
BLACK = 1

def int2color(colornr):
    color_dict = {0: "nocolor", 1: "black", 2: "blue", 3: "green", 4: "yellow", 5: "red", 6: "white", 7: "brown"}
    return color_dict[colornr]


def set_leds_color(leds, color):
    color = color.upper()
    if color not in ["BLACK", "RED", "GREEN", "AMBER", "ORANGE", "YELLOW"]:
        color = "AMBER"
    leds.set_color("LEFT", color) 
    leds.set_color("RIGHT", color)


class ArmMotor():
    """
    Wrapper class for the motor, all beahviors should use this class to control the motor.
    In the future if we want to change the type of motor, we only have to change this class
    """
    def __init__(self, motor, base_speed=BASE_SPEED):
        self.motor = motor
        self.base_speed = base_speed
    
    def move(self, up=True, rotations=1, block=False):
        if up:
            self.motor.on_for_rotations(SpeedPercent(self.base_speed), rotations, block=block)
        else:
            self.motor.on_for_rotations(SpeedPercent(-self.base_speed), rotations, block=block)

    def stop(self):
        self.motor.stop()


class Motor():
    """
    Wrapper class for the motor, all beahviors should use this class to control the motor.
    In the future if we want to change the type of motor, we only have to change this class
    """
    def __init__(self, motor, base_speed=BASE_SPEED):
        self.motor = motor
        self.base_speed = base_speed
    
    def run(self, forward=True, rotations=1, block=False):
        if forward:
            self.motor.on_for_rotations(0, SpeedPercent(self.base_speed), rotations, block=block)
        else:
            self.motor.on_for_rotations(0, SpeedPercent(-self.base_speed), rotations, block=block)
    

    def turn(self, direction=None, steer_degrees=180, block=False):
        if direction != None:
            direction = (direction + 180) / 360 * 200 - 100

        self.motor.on_for_degrees(direction, SpeedPercent(self.base_speed), steer_degrees, block=block)
    
    def stop(self):
        self.motor.stop()

    @property
    def is_running(self):
        return self.motor.is_running


class TaskRegistry():
    """
    Class to keep track of tasks that have to be done before the robot can stop.

    Before starting the robot, the main program should add all the tasks that have to be done, 
    so the RunningBhv will check the registry to see if all tasks are done, and if so, stop the robot.
    """
    def __init__(self):
        self.tasks = {}

    def add(self, task_name):
        self.tasks[task_name] = False

    def set(self, task_name, value):
        self.tasks[task_name] = value

    def get(self, task_name):
        return self.tasks[task_name]
    
    def tasks_done(self):
        return all(self.tasks.values())


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

        if self.is_master:
            self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_sock.bind((server_mac, port))
        else:
            self.client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

        self.startup()

    def startup(self):
        """
        Starts the connection between the master and the slave.
        """
        if self.is_master:
            self.server_sock.listen(10)
            if self.debug:
                timedlog('Listening for connections from the slave...')

            client_sock, address = self.server_sock.accept()
            if self.debug:
                timedlog('Accepted connection')
            self.client_sock = client_sock

        else:
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
        @return: The data that was read
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


def read_color_sensor(cs):
    """
    Reads the color sensor and returns the color that was read.
    @param color_sensor: The color sensor to read
    @return: The color that was read
    """
    try:
        color = cs.color
    except: 
        timedlog("Color sensor wrong read")
        return read_color_sensor(cs)
    return int2color(color)

def read_ultrasonic_sensor(ultrasonic_sensor):
    """
    Reads the ultrasonic sensor and returns the distance.
    @param color_sensor: The ultrasonic sensor to read
    @return: The distance that was read
    """
    try:
        distance = ultrasonic_sensor.value()
    except: 
        timedlog("Ultrasonic sensor wrong read")
        return read_ultrasonic_sensor(ultrasonic_sensor)
    return distance

def read_touch_sensor(touch_sensor):
    """
    Reads the touch sensor and returns the distance.
    @param color_sensor: The touch sensor to read
    @return: The touch that was read
    """
    try:
        touch = touch_sensor.is_pressed
    except: 
        timedlog("Touch sensor wrong read")
        return read_touch_sensor(touch_sensor)
    return touch


##########################################################################
##########################################################################
#########################                #################################
#########################  BEHAVIORS.PY  #################################
#########################                #################################
##########################################################################
##########################################################################


class RunningBhv(Behavior):
    """
    Default behavior that will run if no other behavior is running, to keep the robot moving while its completing tasks
    """
    
    def __init__(self, motor, leds=False, task_registry=None):
        """
        Initialize the behavior
        @param motor: the motor to use
        @param leds: the leds to use
        @param task_registry: the task registry to check
        """
        Behavior.__init__(self)
        self.supressed = False
        self.motor = motor
        self.leds = leds
        self.task_registry = task_registry

    def check(self):
        """
        Always returns true if it has task to complete
        @return: True
        @rtype: bool
        """
        if self.task_registry is None:
            return True

        return not self.task_registry.tasks_done()

    def action(self):
        """
        Keep the robot moving
        """

        self.supressed = False
        timedlog("Moving")
        if self.leds:
            set_leds_color(self.leds, "GREEN")
        self.motor.run()

        while self.motor.is_running and not self.supressed:
            pass

        if not self.supressed:
            return True
        else:
            timedlog("Moving suppressed")
            return False

    def suppress(self):
        """
        Suppress the behavior
        """
        self.motor.stop()
        self.supressed = True

class UltrasonicSensorBhv(Behavior):
    """
    This behavior will check if the ultrasonic sensor dedect an object, and makes the robot avoid it
    """
        
    def __init__(self, ultrasonic_sensor, motor, leds=False, sound=False, threshold_distance=50):
        """
        Initialize the behavior
        @param ultrasonic_sensor: The ultrasonic sensor to use
        @param motor: the motor to use
        @param leds: the leds to use
        @param sound: the sound to use

        """
        Behavior.__init__(self)
        self.supressed = False
        ultrasonic_sensor.mode = 'US-DIST-CM'
        self.ultrasonic_sensor = ultrasonic_sensor
        self.motor = motor
        self.leds = leds
        self.sound = sound
        self.threshold_distance = threshold_distance
        self.object_detected = True

    
    def check(self):
        """
        Check if the ultrasonic sensor dedect an object
        @return: True if the ultrasonic sensor dedect an object
        @rtype: bool
        """
        
        object_detected = read_ultrasonic_sensor(self.ultrasonic_sensor) < self.threshold_distance

        if object_detected != self.object_detected:
            self.object_detected = object_detected
            return object_detected
        return False
        

    def action(self):
        """
        Change direction to step away from the object
        """

        self.suppressed = False
        
        self.motor.turn(direction=45)

        while self.motor.is_running and not self.suppressed:
            pass
        if not self.suppressed:
            return True
        else:
            timedlog("Collision avoidance suppressed")
            return False


    def suppress(self):
        """
        Suppress the behavior
        """
        self.motor.stop()
        self.suppressed = True


class ReceiveTouchSensorBhv(Behavior):
    """
    This behavior will check if the robot has recived a reading from the touch sensors
    This behavior is istantaneous, so the supress method doesn't make sense
    """

    def __init__(self, motor, bluetooth_connection, leds=False, sound=False):
        """
        Initialize the behavior
        @param motor: the motor to use
        @param bluetooth_connection: The bluetooth connection to use
        @param leds: the leds to use
        @param sound: the sound to use
 
        """
        Behavior.__init__(self)
        self.motor = motor
        self.bluetooth_connection = bluetooth_connection
        self.leds = leds
        self.sound = sound
        self.direction = None
        self.collision_data = self.bluetooth_connection.get_data().split(" ")

    
    def check(self):
        """
        Check if the bluetooth connection has recived a new reading
        @return: True if the bluetooth connection has recived a new reading
        @rtype: bool
        """
        if self.collision_data:
            if self.collision_data[0] == "TOUCH":
                if self.collision_data[1] == "LEFT":
                    self.direction = 45
                elif self.collision_data[1] == "RIGHT":
                    self.direction = -45
                else:
                    self.direction = 0
            self.collision_data = self.bluetooth_connection.get_data()
            return True

        return False
        

    def action(self):
        """
        Avoid obstacle
        """
        timedlog("Collision detected by other brick: " + self.collision_data)
        if self.leds:
            set_leds_color(self.leds, 'RED')
        if self.sound:
            self.sound.beep()
            self.sound.beep()

        if self.direction:
            self.motor.stop()
            self.motor.turn(direction=self.direction)

        return True


    def suppress(self):
        """
        This behavior is istantaneous, so the supress method doesn't make sense
        """
        pass


class ReceiveUltrasonicSensorBhv(Behavior):
    """
    This behavior will check if the robot has recived a reading from the ulstrasonic sensor
    This behavior is istantaneous, so the supress method doesn't make sense
    """

    def __init__(self, motor, bluetooth_connection, leds=False, sound=False):
        """
        Initialize the behavior
        @param motor: the motor to use
        @param bluetooth_connection: The bluetooth connection to use
        @param leds: the leds to use
        @param sound: the sound to use
 
        """
        Behavior.__init__(self)
        self.motor = motor
        self.bluetooth_connection = bluetooth_connection
        self.leds = leds
        self.sound = sound
        self.direction = None
        self.collision_data = self.bluetooth_connection.get_data().split(" ")

    
    def check(self):
        """
        Check if the bluetooth connection has recived a new reading
        @return: True if the bluetooth connection has recived a new reading
        @rtype: bool
        """
        if self.collision_data:
            self.direction = 45
            self.collision_data = self.bluetooth_connection.get_data()
            return True

        return False
        

    def action(self):
        """
        Avoid obstacle
        """
        timedlog("Collision detected by other brick: " + self.collision_data)
        if self.leds:
            set_leds_color(self.leds, 'RED')
        if self.sound:
            self.sound.beep()
            self.sound.beep()

        if self.direction:
            self.motor.stop()
            self.motor.turn(direction=self.direction)

        return True


    def suppress(self):
        """
        This behavior is istantaneous, so the supress method doesn't make sense
        """
        pass

##########################################################################
##########################################################################
#########################           ######################################
#########################  MAIN.PY  ######################################
#########################           ######################################
##########################################################################
##########################################################################



##### MASTER #####

CS_L, CS_M, CS_R, US_B, M_L, M_R, M_A, LEFT, RIGHT = INPUT_1, INPUT_2, INPUT_3, INPUT_4, OUTPUT_A, OUTPUT_B, OUTPUT_C, -1, 1

cs_l, cs_m, cs_r, us_b, move_steering, arm_steering, leds, s = ColorSensor(CS_L), ColorSensor(CS_M), ColorSensor(CS_R), UltrasonicSensor(US_B), MoveSteering(M_L, M_R), MediumMotor(M_A), Leds(), Sound()

motor = Motor(move_steering)
arm = ArmMotor(arm_steering)

controller = Controller(return_when_no_action=True)

my_display = Display()

master_mac = '78:DB:2F:29:F0:39'
master = False

bluetooth_connection = BluetoothConnection(master, master_mac, debug=True)

task_registry = TaskRegistry()

s.speak('Start')
timedlog("Starting")





##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####





##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####





bluetooth_connection.start_listening(lambda data: ())
controller.start()

s.speak("stop")