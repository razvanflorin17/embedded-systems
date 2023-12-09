import random

from ev3dev2.motor import SpeedPercent, MoveSteering, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.display import Display
from ev3dev2.sound import Sound
from ev3dev2.led import Leds
from ev3dev2.sensor.lego import ColorSensor, TouchSensor, UltrasonicSensor
from ev3dev2._platform.ev3 import INPUT_1, INPUT_2, INPUT_3, INPUT_4
from ev3devlogging import timedlog

import bluetooth, threading

from Subs_arch import Behavior, Controller
from commons import *


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


class EdgeAvoidanceBhv(Behavior):
    """
    This behavior will check if the robot is on the black border, and tries to step away from it
    """

    def __init__(self, left_cs, mid_cs, right_cs, back_ult, motor, leds=False, sound=False, heigth_treshold=50, edge_color="white"):
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
        self.back_ult = back_ult
        self.motor = motor
        self.leds = leds
        self.sound = sound
        self.heigth_treshold = heigth_treshold        

        self.edge = {"left": False, "mid": False, "right": False}
        self.back_cliff = False
        self.edge_color = edge_color


    
    def check(self):
        """
        Check if the color sensor is on a black surface
        @return: True if the color sensor is on a black surface
        @rtype: bool
        """
        left_edge = read_color_sensor(self.left_cs) == self.edge_color  # note maybe we should check against the table color instead of the edge color
        mid_edge = read_color_sensor(self.mid_cs) == self.edge_color
        right_edge = read_color_sensor(self.right_cs) == self.edge_color
        back_cliff = read_ultrasonic_sensor(self.back_ult) > self.heigth_treshold

        if left_edge != self.edge["left"] or mid_edge != self.edge["mid"] or right_edge != self.edge["right"] or back_cliff != self.back_cliff:
            self.edge["left"] = left_edge
            self.edge["mid"] = mid_edge
            self.edge["right"] = right_edge
            self.back_cliff = back_cliff
            return any([left_edge, mid_edge, right_edge]) # back_cliff is not a valid condition to fire, but it's used to decide how to move

        return False
    

    def _get_operations(self, left, mid, right, back):# todo: ask to chatgpt to generate the best operations (providing the motors operations and the sensors readings)
        
        # [lambda: self.motor.turn(direction=45), lambda: self.motor.turn(direction=right, degrees=30)]  # tipical operations should be like this

        # if all([left, mid, right, back]):  # all sensors on the edge and back cliff (stuck everywhere)
            # return []
        if all([left, mid, right]):  # all sensors on the edge
            random_choice = random.choice(['LEFT', 'RIGHT'])
            return [lambda: self.motor.run(forward=False, distance=10), lambda: self.motor.turn(direction=random_choice, degrees=90)]
        
        # if all([left, right, back]):  # left and right sensors on the edge and back cliff (stuck everywhere)
            # return []
        if all([left, right]):  # left and right sensors on the edge
            random_choice = random.choice(['LEFT', 'RIGHT'])
            return [lambda: self.motor.run(forward=False, distance=10), lambda: self.motor.turn(direction=random_choice, degrees=90)]
        
        if all([left, mid, back]):  # left and mid sensors on the edge and back cliff
            return [lambda: self.motor.turn(direction=RIGHT, degrees=45)]
        if all([left, mid]):  # left and mid sensors on the edge
            return [lambda: self.motor.run(forward=False, distance=10), lambda: self.motor.turn(direction=RIGHT, degrees=100)]
        
        if all([mid, right, back]):  # mid and right sensors on the edge and back cliff
            return [lambda: self.motor.turn(direction=LEFT, degrees=45)]
        if all([mid, right]):  # mid and right sensors on the edge
            return [lambda: self.motor.run(forward=False, distance=10), lambda: self.motor.turn(direction=LEFT, degrees=100)]

        if all([left, back]):  # left sensor on the edge and back cliff
            return [lambda: self.motor.turn(direction=RIGHT, degrees=45)]
        if left:  # left sensor on the edge
            return [lambda: self.motor.run(forward=False, distance=10), lambda: self.motor.turn(direction=RIGHT, degrees=100)]
        
        if all([right, back]):  # right sensor on the edge and back cliff
            return [lambda: self.motor.turn(direction=LEFT, degrees=45)]
        if right:  # right sensor on the edge
            return [lambda: self.motor.run(forward=False, distance=10), lambda: self.motor.turn(direction=RIGHT, degrees=100)]
        
        timedlog("color sensor left: " + str(left))
        timedlog("color sensor mid: " + str(mid))
        timedlog("color sensor right: " + str(right))
        timedlog("ultrasonic back: " + str(back))


    def action(self):
        """
        Change direction to step away from the border
        """

        self.supressed = False
        timedlog("Edge collision")
        if self.leds:
            set_leds_color(self.leds, "BLACK")
        if self.sound:
            self.sound.beep()

        for operation in self._get_operations(self.edge["left"], self.edge["mid"], self.edge["right"], self.back_cliff):
            operation()
            while self.motor.is_running and not self.supressed:
                pass
            if self.supressed:
                break

        if not self.supressed:
            return True
        else:
            timedlog("Edge collision suppressed")
            return False


    def suppress(self):
        """
        Suppress the behavior
        """
        self.motor.stop()
        self.supressed = True



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
        if self.data != data:
            self.data = data
            timedlog("Readings: " + self.data)
            return True
        
        return False
            
    def action(self):
        """
        Update the readings dictionary with the new readings
        """
        
        data = self.data.split(",")

        self.readings_dict["touch_left"] = bool(data[0])
        self.readings_dict["touch_right"] = bool(data[1])
        self.readings_dict["touch_back"] = bool(data[2])
        self.readings_dict["ult_front"] = int(data[3])

        msg = str(self.readings_dict['touch_left']) + "," + str(self.readings_dict['touch_right']) + "," + str(self.readings_dict['touch_back']) + "," + str(self.readings_dict['ult_front'])
        log = "Readings: " + msg
        timedlog(log)



    def suppress(self):
        """
        Suppress the behavior
        """
        pass




# class UltrasonicSensorBhv(Behavior):
#     """
#     This behavior will check if the ultrasonic sensor dedect an object, and makes the robot avoid it
#     """
        
#     def __init__(self, ultrasonic_sensor, motor, leds=False, sound=False, threshold_distance=50):
#         """
#         Initialize the behavior
#         @param ultrasonic_sensor: The ultrasonic sensor to use
#         @param motor: the motor to use
#         @param leds: the leds to use
#         @param sound: the sound to use

#         """
#         Behavior.__init__(self)
#         self.supressed = False
#         ultrasonic_sensor.mode = 'US-DIST-CM'
#         self.ultrasonic_sensor = ultrasonic_sensor
#         self.motor = motor
#         self.leds = leds
#         self.sound = sound
#         self.threshold_distance = threshold_distance
#         self.object_detected = True

    
#     def check(self):
#         """
#         Check if the ultrasonic sensor dedect an object
#         @return: True if the ultrasonic sensor dedect an object
#         @rtype: bool
#         """
        
#         object_detected = read_ultrasonic_sensor(self.ultrasonic_sensor) < self.threshold_distance

#         if object_detected != self.object_detected:
#             self.object_detected = object_detected
#             return object_detected
#         return False
        

#     def action(self):
#         """
#         Change direction to step away from the object
#         """

#         self.suppressed = False
        
#         self.motor.turn(direction=45)

#         while self.motor.is_running and not self.suppressed:
#             pass
#         if not self.suppressed:
#             return True
#         else:
#             timedlog("Collision avoidance suppressed")
#             return False


#     def suppress(self):
#         """
#         Suppress the behavior
#         """
#         self.motor.stop()
#         self.suppressed = True


# # class ReceiveTouchSensorBhv(Behavior):
#     """
#     This behavior will check if the robot has recived a reading from the touch sensors
#     This behavior is istantaneous, so the supress method doesn't make sense
#     """

#     def __init__(self, motor, bluetooth_connection, leds=False, sound=False):
#         """
#         Initialize the behavior
#         @param motor: the motor to use
#         @param bluetooth_connection: The bluetooth connection to use
#         @param leds: the leds to use
#         @param sound: the sound to use
 
#         """
#         Behavior.__init__(self)
#         self.motor = motor
#         self.bluetooth_connection = bluetooth_connection
#         self.leds = leds
#         self.sound = sound
#         self.direction = None
#         self.collision_data = self.bluetooth_connection.get_data().split(" ")

    
#     def check(self):
#         """
#         Check if the bluetooth connection has recived a new reading
#         @return: True if the bluetooth connection has recived a new reading
#         @rtype: bool
#         """
#         if self.collision_data:
#             if self.collision_data[0] == "TOUCH":
#                 if self.collision_data[1] == "LEFT":
#                     self.direction = 45
#                 elif self.collision_data[1] == "RIGHT":
#                     self.direction = -45
#                 else:
#                     self.direction = 0
#             self.collision_data = self.bluetooth_connection.get_data()
#             return True

#         return False
        

#     def action(self):
#         """
#         Avoid obstacle
#         """
#         timedlog("Collision detected by other brick: " + self.collision_data)
#         if self.leds:
#             set_leds_color(self.leds, 'RED')
#         if self.sound:
#             self.sound.beep()
#             self.sound.beep()

#         if self.direction:
#             self.motor.stop()
#             self.motor.turn(direction=self.direction)

#         return True


#     def suppress(self):
#         """
#         This behavior is istantaneous, so the supress method doesn't make sense
#         """
#         pass



# class ReceiveUltrasonicSensorBhv(Behavior):
#     """
#     This behavior will check if the robot has recived a reading from the ulstrasonic sensor
#     This behavior is istantaneous, so the supress method doesn't make sense
#     """

#     def __init__(self, motor, bluetooth_connection, leds=False, sound=False):
#         """
#         Initialize the behavior
#         @param motor: the motor to use
#         @param bluetooth_connection: The bluetooth connection to use
#         @param leds: the leds to use
#         @param sound: the sound to use
 
#         """
#         Behavior.__init__(self)
#         self.motor = motor
#         self.bluetooth_connection = bluetooth_connection
#         self.leds = leds
#         self.sound = sound
#         self.direction = None
#         self.collision_data = self.bluetooth_connection.get_data().split(" ")

    
#     def check(self):
#         """
#         Check if the bluetooth connection has recived a new reading
#         @return: True if the bluetooth connection has recived a new reading
#         @rtype: bool
#         """
#         if self.collision_data:
#             self.direction = 45
#             self.collision_data = self.bluetooth_connection.get_data()
#             return True

#         return False
        

#     def action(self):
#         """
#         Avoid obstacle
#         """
#         timedlog("Collision detected by other brick: " + self.collision_data)
#         if self.leds:
#             set_leds_color(self.leds, 'RED')
#         if self.sound:
#             self.sound.beep()
#             self.sound.beep()

#         if self.direction:
#             self.motor.stop()
#             self.motor.turn(direction=self.direction)

#         return True


#     def suppress(self):
#         """
#         This behavior is istantaneous, so the supress method doesn't make sense
#         """
#         pass