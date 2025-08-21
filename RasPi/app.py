#!/bin/python3
import argparse
import config
import secrets

# Parse arguments before anything for faster feedback
parser = argparse.ArgumentParser()
parser.add_argument("connection", nargs='?', help="Device Connection String from Azure", 
                    default=config.IOTHUB_DEVICE_CONNECTION_STRING)
parser.add_argument("-t", "--time", type=int, default=config.MESSAGE_TIMESPAN,
                    help="Time in between messages sent to IoT Hub, in milliseconds (default: 2000ms)")
parser.add_argument("-n", "--no-send", action="store_true", 
                    help="Disable sending data to IoTHub, only print to console")
parser.add_argument("-mu", "--mqtt-user", type=str, help="MQTT username, if not set will use secrets.MQTT_USER",
                    default=secrets.MQTT_USER if hasattr(secrets, 'MQTT_USER') else None)
parser.add_argument("-mp", "--mqtt-pass", type=str, help="MQTT password, if not set will use secrets.MQTT_PASS",
                    default=secrets.MQTT_PASS if hasattr(secrets, 'MQTT_PASS') else None)
parser.add_argument("-mh", "--mqtt-host", type=str, help="MQTT host, if not set will use config.MQTT_HOST",
                    default=config.MQTT_HOST if hasattr(config, 'MQTT_HOST') else None)
parser.add_argument("-mpo", "--mqtt-port", type=int, help="MQTT port, if not set will use config.MQTT_PORT",
                    default=config.MQTT_PORT if hasattr(config, 'MQTT_PORT') else 1883)
parser.add_argument("-mt", "--mqtt-topic", type=str, help="MQTT topic, if not set will use config.MQTT_TOPIC",
                    default=config.MQTT_TOPIC if hasattr(config, 'MQTT_TOPIC') else "iot/bme280/esp32")

ARGS = parser.parse_args()

from azure.iot.device import IoTHubDeviceClient
from azure.iot.device import Message
from azure.iot.device.exceptions import ConnectionFailedError, ConnectionDroppedError, OperationTimeout, OperationCancelled, NoConnectionError
from log import console, log
from dotenv import load_dotenv
import json
import time
import sqlite3
import paho.mqtt.client as mqtt

load_dotenv()

# ============ DB SETUP ============
def setup_database():
    """
    Set up the SQLite database to store BME280 data.
    Stores device_ts, temp_c, hum_pct, pres_hpa
    """
    conn = sqlite3.connect('bme280_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bme280_data (
            device_ts INTEGER PRIMARY KEY,
            temp_c REAL NOT NULL,
            hum_pct REAL NOT NULL,
            pres_hpa REAL NOT NULL
        )
    ''')
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_state (
            key   TEXT PRIMARY KEY,
            value INTEGER
        )
    """)
    conn.commit()
    conn.close()

def get_sync_state():
    """
    Get the last sync state from the database.
    Returns the last synced timestamp or None if not found.
    """
    conn = sqlite3.connect('bme280_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM sync_state WHERE key='last_sync_ts'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_sync_state(ts):
    """
    Set the last sync state in the database.
    """
    conn = sqlite3.connect('bme280_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO sync_state (key, value) VALUES ('last_sync_ts', ?)", (ts,))
    conn.commit()
    conn.close()

def fetch_rows_newer_than(ts, limit=5000):
    conn = sqlite3.connect('bme280_data.db')
    c = conn.cursor()
    c.execute("""
        SELECT device_ts, temp_c, hum_pct, pres_hpa
        FROM bme280_data
        WHERE device_ts > ?
        ORDER BY device_ts ASC
        LIMIT ?
    """, (int(ts), int(limit)))
    rows = c.fetchall()
    conn.close()
    return rows
# ============ END DB SETUP ============


# ============ MQTT ============
def on_connect(client, userdata, flags, rc):
    """
    Callback function for when the MQTT client connects to the broker.
    """
    log.success("Connected to MQTT broker", client._host, "with result code", rc)
    client.subscribe(ARGS.mqtt_topic)

def on_message(client, userdata, msg):
    """
    Callback function for when a message is received from the MQTT broker.
    """
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        log.info("Received message:", payload)
        device_ts = int(payload["device_ts"])
        temp_c    = float(payload["temp_c"])
        hum_pct   = float(payload["hum_pct"])
        pres_hpa  = float(payload["pres_hpa"])

        # Store data in SQLite database
        conn = sqlite3.connect('bme280_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO bme280_data (device_ts, temp_c, hum_pct, pres_hpa)
            VALUES (?, ?, ?, ?)
        ''', (device_ts, temp_c, hum_pct, pres_hpa))
        conn.commit()
        conn.close()
        
        log.info("Stored to DB", {
            "device_ts": device_ts, "temp_c": temp_c, "hum_pct": hum_pct, "pres_hpa": pres_hpa
        })

    except (KeyError, ValueError) as e:
        log.error("Bad payload fields:", e)
    except json.JSONDecodeError as e:
        log.error("Failed to decode JSON message:", e)
    except sqlite3.Error as e:
        log.error("Database error:", e)

def start_mqtt_background():
    client = mqtt.Client(client_id="raspberrypi-client")
    if ARGS.mqtt_user:
        client.username_pw_set(ARGS.mqtt_user, ARGS.mqtt_pass)
    client.on_connect = on_connect
    client.on_message = on_message
    log.info(f"MQTT connect -> {ARGS.mqtt_host}:{ARGS.mqtt_port}, topic='{ARGS.mqtt_topic}'")
    client.connect(ARGS.mqtt_host, ARGS.mqtt_port, 60)
    client.loop_start()
    
    return client
# ============ END MQTT ============

# ============ Azure IoT Hub ============
def make_device_client(conn_string):
    """
    Create an instance of the IoTHubDeviceClient using the connection string.
    """
    with console.status("Connecting to IoT Hub with Connection String", spinner="arc", spinner_style="blue"):
        dc = IoTHubDeviceClient.create_from_connection_string(conn_string, connection_retry=False)
        dc.connect()
    log.success("Connected to IoT Hub")
    return dc    

def send_message(device_client: IoTHubDeviceClient, message):
    telemetry = Message(json.dumps(message))
    telemetry.content_encoding = "utf-8"
    telemetry.content_type = "application/json"
    
    try:
        device_client.send_message(telemetry)
        log.success("Message sent to IoT Hub", message)
        return True
    
    except (ConnectionFailedError, ConnectionDroppedError, OperationTimeout, OperationCancelled, NoConnectionError):
        log.warning("Message failed to send, skipping")
        return False
# ============ END Azure IoT Hub ============

# ============ Main ============
def main():
    if not ARGS.connection and not ARGS.no_send:  # If no argument
        log.error("IOTHUB_DEVICE_CONNECTION_STRING in config.py variable or argument not found, try supplying one as an argument or setting it in config.py")
    if not ARGS.mqtt_host or not ARGS.mqtt_port:
        log.error("MQTT host or port not set, use --mqtt-host and --mqtt-port arguments to set them or config.py")
        return
    if not ARGS.mqtt_user:
        log.warning("MQTT user not set")
    if not ARGS.mqtt_pass:
        log.warning("MQTT password not set")
    if not ARGS.mqtt_topic:
        log.warning("MQTT topic not set, use --mqtt-topic argument to set it or config.py")

    print()  # Blank line

    setup_database()  # Ensure the database is set up

    # Start MQTT client in background
    mqtt_client = start_mqtt_background()

    # setup iot hub client if not in no_send mode
    if not ARGS.no_send:
        try:
            device_client = make_device_client(ARGS.connection)
        except Exception as e:
            log.error("Failed to connect to IoT Hub:", e)
            return
        
    # Main loop: read rows newer than last_sent_ts and send (or just print if --no-send)
    last_sent_ts = get_sync_state() or 0  # Default to 0 if no state found
    log.info("Starting sender loop; last_sent_ts =", last_sent_ts)

    try:
        while True:
            rows = fetch_rows_newer_than(last_sent_ts)
            if not rows:
                # nothing new → just wait for the configured interval
                time.sleep(ARGS.time / 1000)
                continue

            # send oldest-first
            for device_ts, temp_c, hum_pct, pres_hpa in rows:
                message = {
                    "DeviceID": "raspberrypi-client",
                    "temperature": temp_c,
                    "humidity": hum_pct,
                    "pressure": pres_hpa,
                    "rasptimestamp": int(time.time()),  # current time in seconds since epoch
                    "device_ts": device_ts
                }

                if ARGS.no_send:
                    log.warning("Not sending to IoTHub", message)
                    # Still advance last_sent_ts (since your criterion is time-based)
                    last_sent_ts = device_ts
                    set_sync_state(last_sent_ts)
                else:
                    if device_client is None:
                        # try reconnect once
                        try:
                            device_client = make_device_client(ARGS.connection)
                        except Exception as e:
                            log.warning("IoT Hub reconnect failed; will retry later:", e)
                            break  # leave loop to sleep then retry

                    # send; on success, advance watermark
                    if send_message(device_client, message):
                        last_sent_ts = device_ts
                        set_sync_state(last_sent_ts)
                    else:
                        # send failed → drop the client so next loop tries reconnect
                        try:
                            device_client.shutdown()
                        except Exception:
                            pass
                        device_client = None
                        # break to back off
                        break

                time.sleep(0.05)

            # wait per your MESSAGE_TIMESPAN/--time before next DB check
            time.sleep(ARGS.time / 1000)

    except KeyboardInterrupt:
        # Shut down the device client when Ctrl+C is pressed
        log.error("Shutting down", exit_after=False)
        device_client.shutdown()


if __name__ == "__main__":
    main()
