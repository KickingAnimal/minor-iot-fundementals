# boot.py -- run on boot-up
from machine import I2C, Pin
import time
import bme280

import secrets

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
bme = bme280.BME280(i2c=i2c)

print("boot.py -- ran on boot-up")