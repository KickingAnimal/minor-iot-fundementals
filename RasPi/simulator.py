import random

class BME280SensorSimulator:

    def __init__(self):
        pass
    
    @property
    def temperature(self):
        return random.uniform(20, 30)

    @property
    def humidity(self):
        return random.uniform(60, 80)
