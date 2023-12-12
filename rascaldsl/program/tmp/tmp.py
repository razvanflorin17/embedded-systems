

class Motor():
    """
    Wrapper class for the differential motor, all beahviors should use this class to control the motor.
    In the future if we want to change the type of motor, we only have to change this class
    """
    def __init__(self, motor, base_speed=BASE_SPEED, initial_momentum=1, momentum_step=0.20, momentum_min=1, momentum_max=1):
    # def __init__(self, motor, base_speed=BASE_SPEED, initial_momentum=1.5, momentum_step=0.20, momentum_min=0.6, momentum_max=1.2):
        self.motor = motor
        self.base_speed = base_speed
        self.initial_momentum = initial_momentum
        self.momentum = initial_momentum
        self.momentum_step = momentum_step
        self.momentum_min = momentum_min
        self.momentum_max = momentum_max
        self.next_momentum = min(self.momentum + 1.5 * self.momentum_step, self.momentum_max)

    def run(self, forward=True, distance=10, speed=None, block=False, brake=True):
        """Runs the motor for a certain distance (cm)"""
        if speed is None:
            speed = self.base_speed * self.momentum
            if forward:
                self.increase_momentum()


        if forward:
            self.motor.on_for_distance(SpeedPercent(speed), distance*10, block=block, brake=brake)
        else:
            self.motor.on_for_distance(SpeedPercent(-speed), distance*10, block=block, brake=brake)

    def increase_momentum(self):
        self.next_momentum = min(self.momentum + 1.5 * self.momentum_step, self.momentum_max)

    def decrease_momentum(self):
        self.next_momentum = max(self.momentum - self.momentum_step, self.momentum_min)


    def apply_momentum(self):
        self.momentum = self.next_momentum

    def turn(self, direction=None, degrees=180, speed=None, block=False):
        self.next_momentum = self.momentum
        if speed is None:
            speed = self.base_speed * self.momentum
            self.decrease_momentum()
            self.apply_momentum()

        if direction == None:
            random_direction = random.choice([LEFT, RIGHT])
            self.turn(random_direction, degrees, speed, block)
        
        elif direction == RIGHT:
            self.motor.turn_right(SpeedPercent(speed), degrees, block=block)
        else:
            self.motor.turn_left(SpeedPercent(speed), degrees, block=block)


    def stop(self):
        self.motor.stop()

    @property
    def is_running(self):
        return self.motor.is_running