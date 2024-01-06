import random

from ev3dev2.motor import MoveDifferential, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.wheel import EV3EducationSetTire
from ev3dev2.sound import Sound
from ev3dev2.led import Leds
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor
from ev3dev2._platform.ev3 import INPUT_1, INPUT_2, INPUT_3, INPUT_4
from Subs_arch import Behavior
from commons import *
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
        self.supressed = False

    def check(self):

        return not TASK_REGISTRY.all_tasks_done()

    def action(self):
        """
        Keep the robot moving
        """

        self.supressed = False
        if DEBUG:
            timedlog("Moving")
        
        # while not self.supressed:
        #     MOTOR.run(forward=True, distance=10, brake=False)
        #     while MOTOR.is_running and not self.supressed:
        #         pass
        #     if not self.supressed:
        #         MOTOR.apply_momentum()

        MOTOR.run(forward=True, distance=1000, brake=False, speedM=1.3)
        while MOTOR.is_running and not self.supressed:
            pass

        return not self.supressed


    def suppress(self):
        """
        Suppress the behavior
        """
        MOTOR.stop()
        self.supressed = True
        if DEBUG:
            timedlog("Moving suppressed")


class CliffAvoidanceBhv(Behavior):
    """
    This behavior will check if the robot is on falling off the cliff
    """

    def __init__(self, heigth_treshold_min=120, heigth_treshold_max=400):
        Behavior.__init__(self)
        self.supressed = False
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
        self.supressed = False
        if DEBUG:
            timedlog("Cliff avoidance " + str(self.back_cliff))

        for operation in self.operations:
            operation()
            while MOTOR.is_running and not self.supressed:
                pass
            if self.supressed:
                break
        
        self._reset()
        if DEBUG and not self.supressed:
            timedlog("Cliff avoidance done")
        return not self.supressed


    def suppress(self):
        """
        Suppress the behavior
        """
        MOTOR.stop()
        self.supressed = True
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
        self.supressed = False

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
        self.supressed = False
        if DEBUG:
            timedlog("Edge collision " + str(self.edge))
        avoid_stuck = [lambda: MOTOR.run(forward=False, distance=10), lambda: MOTOR.turn(degrees=5)] if random.random() < 0.1 else []
        for operation in avoid_stuck + self.operations:
            operation()
            while MOTOR.is_running and not self.supressed:
                pass
            if self.supressed:
                break
        
        self._reset()
        if DEBUG and not self.supressed:
            timedlog("Edge collision done")
        return not self.supressed



    def suppress(self):
        """
        Suppress the behavior
        """
        MOTOR.stop()
        self.supressed = True
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
        self.supressed = False
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

        self.supressed = False
        if DEBUG:
            timedlog("Lake collision  " + str(self.edge))

        avoid_stuck = [lambda: MOTOR.run(forward=False, distance=10), lambda: MOTOR.turn(degrees=5)] if random.random() < 0.1 else []
        for operation in avoid_stuck + self.operations:
            operation()
            while MOTOR.is_running and not self.supressed:
                pass
            # if self.last_color is not None:
            #     self.detected_colors[self.last_color] = True
            #     self.last_color = None
            if self.supressed:
                break
        
        self._reset()
        if DEBUG and not self.supressed:
            timedlog("Lake collision done")
        return not self.supressed


    def suppress(self):
        """
        Suppress the behavior
        """
        MOTOR.stop()
        self.supressed = True
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
        self.supressed = False
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
            while MOTOR.is_running and not self.supressed:
                pass
            if self.supressed:
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
        self.supressed = False
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
            while MOTOR.is_running and not self.supressed:
                pass
            if self.supressed:
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