# boot.py -- run on boot-up
from machine import I2C, Pin
import bme280
import network, time
import secrets
import ntptime

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
bme = bme280.BME280(i2c=i2c)

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASS)
        for _ in range(100):   # ~10s timeout
            if wlan.isconnected():
                break
            time.sleep(0.5)
    if wlan.isconnected():
        print("Wi-Fi connected:", wlan.ifconfig())
    else:
        print("Wi-Fi connection failed")

# ---- Run at boot ----
wifi_connect()

# Sync NTP time
try:
    ntptime.settime()
    print("NTP time synced")
except Exception as e:
    print("NTP sync failed:", e)


print("boot.py -- ran on boot-up")