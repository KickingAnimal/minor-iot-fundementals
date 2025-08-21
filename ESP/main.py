# main.py -- put your code here!
print("main.py... running")

import json, ubinascii, time, secrets, usocket
from umqtt.robust import MQTTClient

# MQTT broker info (your Raspberry Pi)
MQTT_HOST = "pi4b-iot"   # change to your Pi IP
MQTT_PORT = 1883             # 1883 = no TLS
MQTT_TOPIC = b"iot/bme280/esp32"

# LED pin (devboard)
led = Pin(2, Pin.OUT)

def mqtt_connect():
    # Resolve MQTT_HOST to IP address
    try:
        addr_info = usocket.getaddrinfo(MQTT_HOST, MQTT_PORT)[0][-1][0]
        print("Resolved IP for", MQTT_HOST, "(", addr_info, ")")
    except Exception as e:
        print("Could not resolve IP for", MQTT_HOST, ":", e)
        addr_info = None

    wlan = network.WLAN(network.STA_IF)
    mac  = ubinascii.hexlify(wlan.config('mac')).decode()  # e.g. "a4cf12ff01ab"
    cid  = "esp32-" + mac                                  # string, safe ASCII
    cid = cid.encode()                               # bytes for umqtt
    
    client = MQTTClient(
        client_id=cid,
        server=MQTT_HOST,
        port=MQTT_PORT,
        user=secrets.MQTT_USER,
        password=secrets.MQTT_PASS,
        keepalive=10
    )
    
    client.connect()
    
    print("Connected to MQTT broker:", MQTT_HOST, "(", addr_info if addr_info else "unknown IP" , ")")
    
    return client

def main():
    print("Starting main loop...")

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
        if seq > 100: #resync ntp
            try:
                ntptime.settime()
                print("NTP time synced")
                print("Current time (UTC):", time.localtime())
            except Exception as e:
                print("NTP sync failed:", e)
            seq = 0
       
        try:
            t, p, h = bme.read_compensated_data()
            current_timestamp = int(time.time())  # get current time
            payload = {
                "temp_c": t,
                "hum_pct": h,
                "pres_hpa": p,
                "device_ts": current_timestamp,  # epoch UTC
            }
            msg = json.dumps(payload)

            # Flash LED while sending
            led.value(1)
            
            try:
                client.publish(MQTT_TOPIC, msg)
                print("Published:", msg)
            except Exception as e:
                print("Publish error:", e)
                # flash led multiple times on error
                for _ in range(10):
                    led.value(1)
                    time.sleep(0.1)
                    led.value(0)
                    time.sleep(0.1)
            
            time.sleep(0.05) 
            led.value(0)

            seq += 1
            while int(time.time()) < current_timestamp + 10:  # wait 10 seconds before next reading
                pass
            
        except Exception as e:
            print("Error:", e)
            time.sleep(5)

main()