#!/usr/bin/env python3


from Subs_arch import Controller
from commons import *
from Behaviors_master import *
if DEBUG:
    from ev3devlogging import timedlog


CONTROLLER = Controller(return_when_no_action=True)


master_mac = '00:17:E9:B4:CE:E6'
master = True

# bluetooth_connection = BluetoothConnection(master, master_mac, debug=DEBUG)


# task_registry = TaskRegistry()

S.speak('Start')
if DEBUG:
    timedlog("Starting")





##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####

# controller.add(UpdateSlaveReadings(bluetooth_connection, readings_dict))
CONTROLLER.add(UpdateReadings())
CONTROLLER.add(CliffAvoidanceBhv())
CONTROLLER.add(EdgeAvoidanceBhv())
CONTROLLER.add(LakeAvoidanceBhv())
# CONTROLLER.add(RecoverCollisionBhv(readings_dict, motor))
# controller.add(AvoidCollisionBhv(readings_dict, motor))
CONTROLLER.add(RunningBhv())


##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####
##### GENERATED CODE GOES HERE #####


# bluetooth_connection.start_listening(lambda data: ())
CONTROLLER.start()

S.speak("stop")