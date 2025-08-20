# main.py -- put your code here!
print("main.py... running")

import json
from umqtt.robust import MQTTClient

# MQTT broker info (your Raspberry Pi)
MQTT_HOST = "pi4b-iot"   # change to your Pi IP
MQTT_PORT = 1883             # 1883 = no TLS
MQTT_TOPIC = b"iot/bme280/esp32"

# LED pin (devboard)
led = Pin(2, Pin.OUT)

def mqtt_connect():
    print("Connecting to MQTT broker:", MQTT_HOST)
    wlan = network.WLAN(network.STA_IF)
    cid = b"esp32-" + wlan.config('mac')
    client = MQTTClient(
        client_id=cid,
        server=MQTT_HOST,
        port=MQTT_PORT,
        user=secrets.MQTT_USER,
        password=secrets.MQTT_PASS,
        keepalive=60
    )
    client.connect()
    print("Connected to MQTT broker:", MQTT_HOST)
    return client

def main():
    while True:
        try:
            client = mqtt_connect()
            break
        except Exception as e:
            print("MQTT connection error:", e)
            print("\nCurrent BME280 data:")
            print(bme.values)
            print("\nRetrying in 5 seconds...\n")
            time.sleep(5)
    seq = 0
    while True:
        try:
            t, p, h = bme.read_compensated_data()
            payload = {
                "temp_c": t,
                "hum_pct": h,
                "pres_hpa": p,
                "device_ts": int(time.time()),  # epoch UTC
                "seq": seq
            }
            msg = json.dumps(payload)

            # Flash LED while sending
            led.value(1)
            client.publish(MQTT_TOPIC, msg)
            led.value(0)

            print("Published:", msg)
            seq += 1
            time.sleep(5)
        except Exception as e:
            print("Error:", e)
            time.sleep(5)

main()