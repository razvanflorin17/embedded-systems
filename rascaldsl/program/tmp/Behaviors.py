from Subs_arch import Behavior
from ev3dev2.sensor.lego import ColorSensor, TouchSensor
from ev3dev2.motor import MoveSteering, OUTPUT_A, OUTPUT_D, SpeedPercent
from ev3dev2.sound import Sound
from ev3dev2.led import Leds
from ev3devlogging import timedlog

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



class ColorSensorBhv(Behavior):
    """
    This behavior will check if the robot is on the black border, and tries to step away from it
    """

    def __init__(self, color_sensor, motor, leds=False, sound=False):
        """
        Initialize the behavior
        @param color_sensor: The color sensor to use
        @param motor: the motor to use
        @param leds: the leds to use
        @param sound: the sound to use
 
        """
        Behavior.__init__(self)
        self.supressed = False
        self.color_sensor = color_sensor
        self.motor = motor
        self.leds = leds
        self.sound = sound
        self.prev_color = None

    
    def check(self):
        """
        Check if the color sensor is on a black surface
        @return: True if the color sensor is on a black surface
        @rtype: bool
        """
        try:
            color = self.color_sensor.color
        except:
            timedlog("Color sensor wrong read")
            return self.check()


        if color != self.prev_color:
            self.prev_color = color
            return color == BLACK

        return False
        

    def action(self):
        """
        Change direction to step away from the border
        """

        self.supressed = False
        stop_conditions = {"suppressed": self.supressed}
        timedlog("Edge collision")
        if self.leds:
            set_leds_color(self.leds, "BLACK")
        if self.sound:
            self.sound.beep()

        self.motor.change_direction(stop_conditions)

        while self.motor.is_running and not self.supressed:
            pass

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


class TouchSensorsBhv(Behavior):
    """
    This behavior will check if the robot touch an object, and tries to step away from it
    """
    
    def __init__(self, touch_sensor_left, touch_sensor_right, motor, leds=False, sound=False):
        """
        Initialize the behavior
        @param touch_sensor: The touch sensor to use
        @param touch_sensor_pos: The position of the sensor on the robot
        @param motor: the motor to use
        @param leds: the leds to use
        @param sound: the sound to use

        """
        Behavior.__init__(self)
        self.supressed = False
        self.touch_sensor_left = touch_sensor_left
        self.touch_sensor_right = touch_sensor_right
        self.motor = motor
        self.leds = leds
        self.sound = sound
        self.pressed_left = False
        self.pressed_right = False

    
    def check(self):
        """
        Check if the touch sensor is pressed
        @return: True if the touch sensor is pressed
        @rtype: bool
        """
        pressed_left, pressed_right = False, False
        try:
            pressed_left = self.touch_sensor_left.is_pressed
        except:
            pressed_left = True
            
        try:
            pressed_right = self.touch_sensor_right.is_pressed
        except:
            pressed_right = True
        
        if pressed_left != self.pressed_left and pressed_right != self.pressed_right:
            self.pressed_left = pressed_left
            self.pressed_right = pressed_right
            return self.pressed_left or self.pressed_right

        elif pressed_left != self.pressed_left:
            self.pressed_left = pressed_left
            return self.pressed_left

        elif pressed_right != self.pressed_right:
            self.pressed_right = pressed_right
            return self.pressed_right
        
        return False
        

    def action(self):
        """
        Change direction to step away from the object
        """

        self.supressed = False
        stop_conditions = {"suppressed": self.supressed}
        timedlog("Collision")
        if self.leds:
            set_leds_color(self.leds, "RED")
        if self.sound:
            self.sound.beep()

        if self.pressed_left and self.pressed_right:
            self.motor.change_direction(stop_conditions)
        elif self.pressed_left:
            self.motor.change_direction(stop_conditions, direction=RIGHT, steer_degrees=120)
        else:
            self.motor.change_direction(stop_conditions, direction=LEFT, steer_degrees=120)

        while self.motor.is_running and not self.supressed:
            pass

        if not self.supressed:
            return True
        else:
            timedlog("Collision suppressed")
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
        
    def __init__(self, ultrasonic_sensor, motor, leds=False, sound=False, threshold_distance=300):
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
        self.object_detected = False

    
    def check(self):
        """
        Check if the ultrasonic sensor dedect an object
        @return: True if the ultrasonic sensor dedect an object
        @rtype: bool
        """
        try:
            object_detected = self.ultrasonic_sensor.value() < self.threshold_distance
        except:
            timedlog("Ultrasonic sensor wrong read")
            return self.check()
        
        if object_detected != self.object_detected:
            self.object_detected = object_detected
            return object_detected
        return False
        

    def action(self):
        """
        Change direction to step away from the object
        """

        self.supressed = False
        stop_conditions = {"suppressed": self.supressed}

        timedlog("Avoiding collision")
        if self.leds:
            set_leds_color(self.leds, "ORANGE")
        if self.sound:
            self.sound.beep()

        self.motor.change_direction(stop_conditions, steer_degrees=90, back_rotations=0.3)

        while self.motor.is_running and not self.supressed:
            pass

        if not self.supressed:
            return True
        else:
            timedlog("Avoiding collision suppressed")
            return False


    def suppress(self):
        """
        Suppress the behavior
        """
        self.motor.stop()
        self.supressed = True


class DetectColorBhv(Behavior):
    """
    This behavior will check if the robot has detected a new color, then will update the color dictionary, and communicate the new color to the other robot
    This behavior is istantaneous, so the supress method doesn't make sense
    """

    def __init__(self, color_sensor, color_dict, bluetooth_connection,leds=False, sound=False):
        """
        Initialize the behavior
        @param color_sensor: The color sensor to use
        @param color_dict: The dictionary of colors to update
        @param leds: the leds to use
        @param sound: the sound to use
 
        """
        Behavior.__init__(self)
        self.color_sensor = color_sensor
        self.color_dict = color_dict
        self.bluetooth_connection = bluetooth_connection
        self.leds = leds
        self.sound = sound

        self.prev_color = None
        self.color_detected = None

    
    def check(self):
        """
        Check if the color sensor is on a new color
        @return: True if the color sensor detected a new color
        @rtype: bool
        """

        try:
            color = self.color_sensor.color
        except:
            timedlog("Color sensor wrong read")
            return self.check()

        if color != self.prev_color:
            self.prev_color = color
            color_str = int2color(color)
            
            if color_str in self.color_dict and self.color_dict[color_str] is False:
                self.color_detected = color_str
                return True

        return False
        

    def action(self):
        """
        Update the color dictionary, and communicate the new color to the other robot
        """
        timedlog("New color detected: " + self.color_detected)
        if self.leds:
            set_leds_color(self.leds, self.color_detected.upper()) # TODO: controllare che i led rimangano accesi, altrimenti aggiungere una sorta di sleep sopprimibile
        if self.sound:
            self.sound.beep()
            self.sound.beep()


        self.color_dict[self.color_detected] = True
        self.bluetooth_connection.write(self.color_detected)

        return True


    def suppress(self):
        """
        This behavior is istantaneous, so the supress method doesn't make sense
        """
        pass

class ReceiveDetectedColorBhv(Behavior):
    """
    This behavior will check if the robot has recived a new detected color, then will update the color dictionary
    This behavior is istantaneous, so the supress method doesn't make sense
    """

    def __init__(self, color_dict, bluetooth_connection, leds=False, sound=False):
        """
        Initialize the behavior
        @param color_dict: The dictionary of colors to update
        @param bluetooth_connection: The bluetooth connection to use
        @param leds: the leds to use
        @param sound: the sound to use
 
        """
        Behavior.__init__(self)
        self.color_dict = color_dict
        self.bluetooth_connection = bluetooth_connection
        self.leds = leds
        self.sound = sound

        self.color_detected = self.bluetooth_connection.get_data()

    
    def check(self):
        """
        Check if the bluetooth connection has recived a new color
        @return: True if the bluetooth connection has recived a new color
        @rtype: bool
        """
        if self.color_detected != self.bluetooth_connection.get_data():
            self.color_detected = self.bluetooth_connection.get_data()
            return True

        return False
        

    def action(self):
        """
        Update the color dictionary
        """
        timedlog("Color detected by other robot: " + self.color_detected)
        if self.leds:
            set_leds_color(self.leds, self.color_detected.upper()) # TODO: controllare che i led rimangano accesi, altrimenti aggiungere una sorta di sleep sopprimibile
        if self.sound:
            self.sound.beep()
            self.sound.beep()

        self.color_dict[self.color_detected] = True

        return True


    def suppress(self):
        """
        This behavior is istantaneous, so the supress method doesn't make sense
        """
        pass

class UpdateColorTaskBhv(Behavior):
    """
    This behavior will check if all the colors have been detected, then will update the task registry
    This behavior is istantaneous, so the supress method doesn't make sense
    """

    def __init__(self, color_dict, task_registry, task_name, leds=False, sound=False):
        """
        Initialize the behavior
        @param color_dict: The dictionary of colors to update
        @param task_registry: The task registry to update
        @param task_name: The name of the task to update
        @param leds: the leds to use
        @param sound: the sound to use
 
        """
        Behavior.__init__(self)
        self.color_dict = color_dict
        self.task_registry = task_registry
        self.leds = leds
        self.sound = sound
        self.task_name = task_name


    
    def check(self):
        """
        Check if the all the colors have been detected, and the task registry has not been updated yet
        @return: True if the bluetooth connection has recived a new color
        @rtype: bool
        """
        return not self.task_registry.get(self.task_name) and all(self.color_dict.values());
        

    def action(self):
        """
        Update the task registry, and make some noise / light
        """
        timedlog("Detected all colors:")
        if self.leds:
            set_leds_color(self.leds, "GREEN") # TODO: controllare che i led rimangano accesi, altrimenti aggiungere una sorta di sleep sopprimibile
        if self.sound:
            self.sound.beep()
            self.sound.beep()
            self.sound.beep()
            self.sound.beep()

        self.task_registry.set(self.task_name, True)

        return True


    def suppress(self):
        """
        This behavior is istantaneous, so the supress method doesn't make sense
        """
        pass

