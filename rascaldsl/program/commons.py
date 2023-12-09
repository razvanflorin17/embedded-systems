#!/usr/bin/env python3

import random
from ev3dev2.motor import SpeedPercent
from ev3dev2.sound import Sound
from ev3devlogging import timedlog
import bluetooth, threading


SOUND_NO_BLOCK = Sound.PLAY_NO_WAIT_FOR_COMPLETE # sound option that doesn't block the program
BASE_SPEED = 15
LEFT, RIGHT = -1, 1
BLACK = 1

def int2color(colornr):
    color_dict = {0: "nocolor", 1: "black", 2: "blue", 3: "green", 4: "yellow", 5: "red", 6: "white", 7: "brown"}
    return color_dict[colornr]


def set_leds_color(leds, color):
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
    Wrapper class for the differential motor, all beahviors should use this class to control the motor.
    In the future if we want to change the type of motor, we only have to change this class
    """
    def __init__(self, motor, base_speed=BASE_SPEED):
        self.motor = motor
        self.base_speed = base_speed
    
    def run(self, forward=True, distance=10, speed=None, block=False):
        """Runs the motor for a certain distance (cm)"""
        if speed is None:
            speed = self.base_speed

        if forward:
            self.motor.on_for_distance(SpeedPercent(speed), distance*10, block=block)
        else:
            self.motor.on_for_distance(SpeedPercent(-speed), distance*10, block=block)

    def turn(self, direction=RIGHT, degrees=180, speed=None, block=False):
        if speed is None:
            speed = self.base_speed

        if direction == RIGHT:
            self.motor.turn_right(SpeedPercent(speed), degrees, block=block)
        else:
            self.motor.turn_left(SpeedPercent(speed), degrees, block=block)


        
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
