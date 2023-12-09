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

from Subs_arch import Behavior, Controller
from commons import *



class UpdateSlaveReadings(Behavior):
    """
    This behavior will check if the robot touch an object, and tries to step away from it
    """
    
    def __init__(self, touch_left, touch_right, touch_back, ult_front, bluetooth_connection, readings_dict):
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
        self.touch_left = touch_left
        self.touch_right = touch_right
        self.touch_back = touch_back
        self.ult_front = ult_front

        self.bluetooth_connection = bluetooth_connection
        self.readings_dict = readings_dict

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

        self.readings_dict["touch_left"] = self.touch_left.is_pressed
        self.readings_dict["touch_right"] = self.touch_right.is_pressed
        self.readings_dict["touch_back"] = self.touch_back.is_pressed
        self.readings_dict["ult_front"] = read_ultrasonic_sensor(self.ult_front)

        msg = str(self.readings_dict['touch_left']) + "," + str(self.readings_dict['touch_right']) + "," + str(self.readings_dict['touch_back']) + "," + str(self.readings_dict['ult_front'])
        log = "Sending Readings: " + msg
        timedlog(log)
        self.bluetooth_connection.write(msg)
        
        time.sleep(0.05)

        return True


    def suppress(self):
        """
        Suppress the behavior
        """
        pass


# class TouchSensorsBhv(Behavior):
#     """
#     This behavior will check if the robot touch an object, and tries to step away from it
#     """
    
#     def __init__(self, touch_sensor_left, touch_sensor_right, motor, leds=False, sound=False):
#         """
#         Initialize the behavior
#         @param touch_sensor: The touch sensor to use
#         @param touch_sensor_pos: The position of the sensor on the robot
#         @param motor: the motor to use
#         @param leds: the leds to use
#         @param sound: the sound to use

#         """
#         Behavior.__init__(self)
#         self.supressed = False
#         self.touch_sensor_left = touch_sensor_left
#         self.touch_sensor_right = touch_sensor_right
#         self.motor = motor
#         self.leds = leds
#         self.sound = sound
#         self.pressed_left = False
#         self.pressed_right = False

    
#     def check(self):
#         """
#         Check if the touch sensor is pressed
#         @return: True if the touch sensor is pressed
#         @rtype: bool
#         """
#         pressed_left, pressed_right = False, False
#         try:
#             pressed_left = self.touch_sensor_left.is_pressed
#         except:
#             pressed_left = True
            
#         try:
#             pressed_right = self.touch_sensor_right.is_pressed
#         except:
#             pressed_right = True
        
#         if pressed_left != self.pressed_left and pressed_right != self.pressed_right:
#             self.pressed_left = pressed_left
#             self.pressed_right = pressed_right
#             return self.pressed_left or self.pressed_right

#         elif pressed_left != self.pressed_left:
#             self.pressed_left = pressed_left
#             return self.pressed_left

#         elif pressed_right != self.pressed_right:
#             self.pressed_right = pressed_right
#             return self.pressed_right
        
#         return False
        

#     def action(self):
#         """
#         Change direction to step away from the object
#         """

#         self.supressed = False
#         stop_conditions = {"suppressed": self.supressed}
#         timedlog("Collision")
#         if self.leds:
#             set_leds_color(self.leds, "RED")
#         if self.sound:
#             self.sound.beep()

#         if self.pressed_left and self.pressed_right:
#             self.motor.change_direction(stop_conditions)
#         elif self.pressed_left:
#             self.motor.change_direction(stop_conditions, direction=RIGHT, steer_degrees=120)
#         else:
#             self.motor.change_direction(stop_conditions, direction=LEFT, steer_degrees=120)

#         while self.motor.is_running and not self.supressed:
#             pass

#         if not self.supressed:
#             return True
#         else:
#             timedlog("Collision suppressed")
#             return False


#     def suppress(self):
#         """
#         Suppress the behavior
#         """
#         self.motor.stop()
#         self.supressed = True


# class DetectObjectSensorBhv(Behavior):
#     """
#     This behavior will check if the ultrasonic sensor dedect an object, and makes the robot avoid it
#     """
        
#     def __init__(self, ultrasonic_sensor, motor, leds=False, sound=False, threshold_distance=300):
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
#         self.object_detected = False

    
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

#         self.supressed = False
#         stop_conditions = {"suppressed": self.supressed}

#         timedlog("Avoiding collision")
#         if self.leds:
#             set_leds_color(self.leds, "ORANGE")
#         if self.sound:
#             self.sound.beep()

#         self.motor.change_direction(stop_conditions, steer_degrees=90, back_rotations=0.3)

#         while self.motor.is_running and not self.supressed:
#             pass

#         if not self.supressed:
#             return True
#         else:
#             timedlog("Avoiding collision suppressed")
#             return False


#     def suppress(self):
#         """
#         Suppress the behavior
#         """
#         self.motor.stop()
#         self.supressed = True


# class DetectColorBhv(Behavior):
#     """
#     This behavior will check if the robot has detected a new color, then will update the color dictionary, and communicate the new color to the other robot
#     This behavior is istantaneous, so the supress method doesn't make sense
#     """

#     def __init__(self, color_sensor, color_dict, leds=False, sound=False):
#         """
#         Initialize the behavior
#         @param color_sensor: The color sensor to use
#         @param color_dict: The dictionary of colors to update
#         @param leds: the leds to use
#         @param sound: the sound to use
 
#         """
#         Behavior.__init__(self)
#         self.color_sensor = color_sensor
#         self.color_dict = color_dict
#         self.leds = leds
#         self.sound = sound

#         self.prev_color = None
#         self.color_detected = None

    
#     def check(self):
#         """
#         Check if the color sensor is on a new color
#         @return: True if the color sensor detected a new color
#         @rtype: bool
#         """

#         try:
#             color = self.color_sensor.color
#         except:
#             timedlog("Color sensor wrong read")
#             return self.check()

#         if color != self.prev_color:
#             self.prev_color = color
#             color_str = int2color(color)
            
#             if color_str in self.color_dict and self.color_dict[color_str] is False:
#                 self.color_detected = color_str
#                 return True

#         return False
        

#     def action(self):
#         """
#         Update the color dictionary, and communicate the new color to the other robot
#         """
#         timedlog("New color detected: " + self.color_detected)
#         if self.leds:
#             set_leds_color(self.leds, self.color_detected.upper())
#         if self.sound:
#             self.sound.beep()
#             self.sound.beep()

#         self.color_dict[self.color_detected] = True

#         return True


#     def suppress(self):
#         """
#         This behavior is istantaneous, so the supress method doesn't make sense
#         """
#         pass

# # class ReceiveDetectedColorBhv(Behavior):
# #     """
# #     This behavior will check if the robot has recived a new detected color, then will update the color dictionary
# #     This behavior is istantaneous, so the supress method doesn't make sense
# #     """

# #     def __init__(self, color_dict, bluetooth_connection, leds=False, sound=False):
# #         """
# #         Initialize the behavior
# #         @param color_dict: The dictionary of colors to update
# #         @param bluetooth_connection: The bluetooth connection to use
# #         @param leds: the leds to use
# #         @param sound: the sound to use
 
# #         """
# #         Behavior.__init__(self)
# #         self.color_dict = color_dict
# #         self.bluetooth_connection = bluetooth_connection
# #         self.leds = leds
# #         self.sound = sound

# #         self.color_detected = self.bluetooth_connection.get_data()

    
# #     def check(self):
# #         """
# #         Check if the bluetooth connection has recived a new color
# #         @return: True if the bluetooth connection has recived a new color
# #         @rtype: bool
# #         """
# #         if self.color_detected != self.bluetooth_connection.get_data():
# #             self.color_detected = self.bluetooth_connection.get_data()
# #             return True

# #         return False
        

# #     def action(self):
# #         """
# #         Update the color dictionary
# #         """
# #         timedlog("Color detected by other robot: " + self.color_detected)
# #         if self.leds:
# #             set_leds_color(self.leds, self.color_detected.upper())
# #         if self.sound:
# #             self.sound.beep()
# #             self.sound.beep()

# #         self.color_dict[self.color_detected] = True

# #         return True


# #     def suppress(self):
# #         """
# #         This behavior is istantaneous, so the supress method doesn't make sense
# #         """
# #         pass
