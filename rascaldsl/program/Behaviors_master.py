import random

from ev3dev2.motor import SpeedPercent, MoveSteering, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.display import Display
from ev3dev2.sound import Sound
from ev3dev2.led import Leds
from ev3dev2.sensor.lego import ColorSensor, TouchSensor, UltrasonicSensor
from ev3dev2._platform.ev3 import INPUT_1, INPUT_2, INPUT_3, INPUT_4
import bluetooth, threading
from Subs_arch import Behavior, Controller
from commons import *
if DEBUG:
    from ev3devlogging import timedlog

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
        if DEBUG:
            timedlog("Moving")
        
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
        """
        Suppress the behavior
        """
        self.motor.stop()
        self.supressed = True
        if DEBUG:
            timedlog("Moving suppressed")


class CliffAvoidanceBhv(Behavior):
    """
    This behavior will check if the robot is on falling off the cliff
    """

    def __init__(self, back_ult, motor, leds=False, sound=False, heigth_treshold=100):
        """
        Initialize the behavior
        @param back_ult: The back ultrasonic sensor to use
        @param motor: the motor to use
        @param leds: the leds to use
        @param sound: the sound to use
        @param heigth_treshold: The treshold distance (from the table) for the ultrasonic sensor
 
        """
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
        """
        Check if the ultrasonic sensor detect a cliff
        @return: True if the ultrasonic sensor detect a cliff
        @rtype: bool
        """
        back_sensor = read_ultrasonic_sensor(self.back_ult)
        back_cliff = back_sensor > self.heigth_treshold

        if back_cliff != self.back_cliff:
            self.back_cliff = back_cliff
            if back_cliff:
                self.operations = self._get_operations(back_cliff)
                return True

        return False
    

    def _get_operations(self, back):
        if back: # back cliff behind the robot
            return [lambda: self.motor.turn(degrees=1), lambda: self.motor.run(forward=True, speedM=0.5, distance=2)]

        if DEBUG:
            timedlog("Back sensors: " + str(back))

        return []


    def action(self):
        """
        Change direction to step away from the border
        """

        # operations = self._get_operations(self.edge["left"], self.edge["mid"], self.edge["right"], self.back_cliff)
        self.supressed = False
        if DEBUG:
            timedlog("Cliff avoidance")

        for operation in self.operations:
            operation()
            while self.motor.is_running and not self.supressed:
                pass
            if self.supressed:
                break
  
        return not self.supressed


    def suppress(self):
        """
        Suppress the behavior
        """
        self.motor.stop()
        self.supressed = True
        if DEBUG:
            timedlog("Cliff avoidance suppressed")


class EdgeAvoidanceBhv(Behavior):
    """
    This behavior will check if the robot is on the black border, and tries to step away from it
    """

    def __init__(self, left_cs, mid_cs, right_cs, motor, leds=False, sound=False, edge_color="white"):
        """
        Initialize the behavior
        @param left_cs: The left color sensor to use
        @param mid_cs: The middle color sensor to use
        @param right_cs: The right color sensor to use
        @param back_ult: The back ultrasonic sensor to use
        @param motor: the motor to use
        @param leds: the leds to use
        @param sound: the sound to use
        @param heigth_treshold: The treshold distance (from the table) for the ultrasonic sensor
 
        """
        Behavior.__init__(self)
        self.supressed = False
        self.left_cs = left_cs
        self.mid_cs = mid_cs
        self.right_cs = right_cs
        self.motor = motor
        self.leds = leds
        self.sound = sound

        self.edge = {"left": False, "mid": False, "right": False}
        self.edge_color = edge_color
        self.operations = []


    
    def check(self):
        """
        Check if the color sensor is on a white surface
        @return: True if the color sensor is on a white surface
        @rtype: bool
        """
        left_c, mid_c, right_c = read_color_sensor(self.left_cs), read_color_sensor(self.mid_cs), read_color_sensor(self.right_cs)

        left_edge = left_c == self.edge_color or left_c == "nocolor"
        mid_edge = mid_c == self.edge_color or mid_c == "nocolor"
        right_edge = right_c == self.edge_color or right_c == "nocolor"


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
            return [lambda: self.motor.run(forward=False, distance=5), lambda: self.motor.turn(degrees=30)]
        
        if all([left, right]):  # left and right sensors on the edge
            return [lambda: self.motor.turn(degrees=45)]
        
        if all([left, mid]):  # left and mid sensors on the edge
            return [lambda: self.motor.run(forward=False, distance=5), lambda: self.motor.turn(direction=RIGHT, degrees=30)]
        
        if all([mid, right]):  # mid and right sensors on the edge
            return [lambda: self.motor.run(forward=False, distance=5), lambda: self.motor.turn(direction=LEFT, degrees=30)]

        if left:  # left sensor on the edge
            return [lambda: self.motor.run(forward=False, distance=2), lambda: self.motor.turn(direction=RIGHT, degrees=15)]
        
        if mid: # mid sensor on the edge
            return [lambda: self.motor.run(forward=False, distance=2), lambda: self.motor.turn(degrees=30)]
        if right:  # right sensor on the edge
            return [lambda: self.motor.run(forward=False, distance=2), lambda: self.motor.turn(direction=LEFT, degrees=15)]

        if DEBUG:
            timedlog("Edge sensors: " + str(left) + " " + str(mid) + " " + str(right))

        return []


    def action(self):
        """
        Change direction to step away from the border
        """

        # operations = self._get_operations(self.edge["left"], self.edge["mid"], self.edge["right"], self.back_cliff)
        self.supressed = False
        if DEBUG:
            timedlog("Edge collision")

        for operation in self.operations:
            operation()
            while self.motor.is_running and not self.supressed:
                pass
            if self.supressed:
                break
        
        return not self.supressed



    def suppress(self):
        """
        Suppress the behavior
        """
        self.motor.stop()
        self.supressed = True
        if DEBUG:
            timedlog("Edge collision suppressed")

class LakeAvoidanceBhv(Behavior):
    """
    This behavior will check if the robot is on a lake, and tries to step away from it
    """

    def __init__(self, left_cs, mid_cs, right_cs, motor, leds=False, sound=False, heigth_treshold=50, lake_colors=["yellow", "blue", "red"]):
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
        self.supressed = False
        self.left_cs = left_cs
        self.mid_cs = mid_cs
        self.right_cs = right_cs
        self.motor = motor
        self.leds = leds
        self.sound = sound
        self.heigth_treshold = heigth_treshold        

        self.edge = {"left": False, "mid": False, "right": False}
        self.lake_colors = lake_colors
        self.operations = []


    
    def check(self):
        """
        Check if the color sensor is on a black surface
        @return: True if the color sensor is on a black surface
        @rtype: bool
        """
        left_edge = read_color_sensor(self.left_cs) in self.lake_colors  # note maybe we should check against the table color instead of the edge color
        mid_edge = read_color_sensor(self.mid_cs) in self.lake_colors
        right_edge = read_color_sensor(self.right_cs) in self.lake_colors

        if left_edge != self.edge["left"] or mid_edge != self.edge["mid"] or right_edge != self.edge["right"]:
            self.edge["left"] = left_edge
            self.edge["mid"] = mid_edge
            self.edge["right"] = right_edge
            
            if any([left_edge, mid_edge, right_edge]):
                self.operations = self._get_operations(left_edge, mid_edge, right_edge)
                return True

        return False
    

    def _get_operations(self, left, mid, right):
        
        if all([left, mid]):  # left and mid sensors on the edge
            return [lambda: self.motor.turn(direction=LEFT, degrees=20), lambda: self.motor.run(forward=False, distance=2)]

    
        if all([mid, right]):  # mid and right sensors on the edge
            return [lambda: self.motor.turn(direction=RIGHT, degrees=20), lambda: self.motor.run(forward=False, distance=2)]

        
        if left:  # left sensor on the edge
            return [lambda: self.motor.turn(direction=RIGHT, degrees=10)]

        if right:  # right sensor on the edge
            return [lambda: self.motor.turn(direction=LEFT, degrees=10)]
        
        
        if mid:  # left sensor on the edge
            return [lambda: self.motor.run(forward=False, distance=5), lambda: self.motor.turn(degrees=30)]

        if DEBUG:
            timedlog("Lake sensors: " + str(left) + " " + str(mid) + " " + str(right) + " ")

        return []

    def action(self):
        """
        Change direction to step away from the border
        """

        # operations = self._get_operations(self.edge["left"], self.edge["mid"], self.edge["right"])
        self.supressed = False
        if DEBUG:
            timedlog("Lake collision")

        for operation in self.operations:
            operation()
            while self.motor.is_running and not self.supressed:
                pass
            if self.supressed:
                break

        return not self.supressed


    def suppress(self):
        """
        Suppress the behavior
        """
        self.motor.stop()
        self.supressed = True
        if DEBUG:
            timedlog("Lake collision suppressed")

class UpdateSlaveReadings(Behavior):
    """
    This simple behavior, at each check cycle, will update the slave readings without doing anything else
    """
        
   
    def __init__(self, bluetooth_connection, readings_dict):
        """
        Initialize the behavior
        @param bluetooth_connection: The bluetooth connection to useù
        @param readings_dict: The readings dictionary to update
        
        """
        Behavior.__init__(self)
        self.bluetooth_connection = bluetooth_connection
        self.readings_dict = readings_dict
        self.data = ""

        self.direction = None

    
    def check(self):
        """
        Check if the bluetooth connection has recived a new reading
        @return: True if the bluetooth connection has recived a new reading
        @rtype: bool
        """

        data = self.bluetooth_connection.get_data()
        if data != "":
            self.data = data
            self._update_readings_dict()
        
        return False
    
    def _update_readings_dict(self):
        data = self.data.split(",")
        self.readings_dict["touch_left"] = bool(int(data[0]))
        self.readings_dict["touch_right"] = bool(int(data[1]))
        self.readings_dict["touch_back"] = bool(int(data[2]))
        self.readings_dict["ult_front"] = int(data[3])

        # log = "Readings: " + str(self.readings_dict['touch_left']) + "," + str(self.readings_dict['touch_right']) + "," + str(self.readings_dict['touch_back']) + "," + str(self.readings_dict['ult_front'])
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
        
    def __init__(self, readings_dict, motor, leds=False, sound=False, threshold_distance=200):
        """
        Initialize the behavior
        @param readings_dict: The readings dictionary to use for the ultrasonic front and touch back
        @param motor: the motor to use
        @param leds: the leds to use
        @param sound: the sound to use

        """
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
        """
        Check if the ultrasonic sensor dedect an object
        @return: True if the ultrasonic sensor dedect an object
        @rtype: bool
        """
        
        obj_front = self.readings_dict["ult_front"] < self.threshold_distance

        if obj_front != self.obj_front:
            self.obj_front = obj_front

            if obj_front:
                self.operations = self._get_operations(obj_front)
                return True
        return False
        

    def _get_operations(self, obj_front):
        if obj_front:
            return [lambda: self.motor.turn(degrees=45)]
            
        
    def action(self):
        """
        Change direction to step away from the object
        """

        self.suppressed = False
        if DEBUG:
            timedlog("Collision avoidance")
        
        for operation in self.operations:
            operation()
            while self.motor.is_running and not self.supressed:
                pass
            if self.supressed:
                break
        
        return not self.suppressed


    def suppress(self):
        """
        Suppress the behavior
        """
        self.motor.stop()
        self.suppressed = True
        if DEBUG:
            timedlog("Collision avoidance suppressed")



class RecoverCollisionBhv(Behavior):
    """
    This behavior will check if we had collide with something, and makes the robot recover from it
    """
        
    def __init__(self, readings_dict, motor, leds=False, sound=False):
        """
        Initialize the behavior
        @param readings_dict: The readings dictionary to use for the touch sensors left and right and touch back
        @param motor: the motor to use
        @param leds: the leds to use
        @param sound: the sound to use

        """
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
        """
        Check if the ultrasonic sensor dedect an object
        @return: True if the ultrasonic sensor dedect an object
        @rtype: bool
        """
        
        obj_left = self.readings_dict["touch_left"]
        obj_right = self.readings_dict["touch_right"]
        obj_back = self.readings_dict["touch_back"]


        if obj_left != self.obj_left or obj_right != self.obj_right or obj_back != self.obj_back:
            self.obj_left = obj_left
            self.obj_right = obj_right
            self.obj_back = obj_back
            
            if any([obj_left, obj_right, obj_back]):
                self.operations = self._get_operations(obj_left, obj_right, obj_back)
                return True

        return False
        

    def _get_operations(self, obj_left, obj_right, obj_back):
        # if all([obj_left, obj_right, obj_back]): # stuck position
            # return []
        if all([obj_left, obj_right]): # left and right sensors touched
            return [lambda: self.motor.run(forward=False, distance=10), lambda: self.motor.turn(degrees=60)]
        if obj_left: # left sensor touched
            return [lambda: self.motor.run(forward=False, distance=5), lambda: self.motor.turn(direction=RIGHT, degrees=60)]
        if obj_right: # right sensor touched
            return [lambda: self.motor.run(forward=False, distance=5), lambda: self.motor.turn(direction=LEFT, degrees=60)]
        if obj_back: # back sensor touched
            return [lambda: self.motor.run(forward=True, distance=5)]
        
            

    def action(self):
        """
        Change direction to step away from the object
        """

        self.suppressed = False
        if DEBUG:
            timedlog("Collision recover")
        
        for operation in self.operations:
            operation()
            while self.motor.is_running and not self.supressed:
                pass
            if self.supressed:
                break

        return not self.suppressed

    def suppress(self):
        """
        Suppress the behavior
        """
        self.motor.stop()
        self.suppressed = True
        if DEBUG:
            timedlog("Collision recover suppressed")