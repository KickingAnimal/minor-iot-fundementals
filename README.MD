# Minor IoT Fundamentals

This project demonstrates a simple IoT pipeline using an **ESP32** with a **BME280 sensor** and a **Raspberry Pi**.

## Overview
- **ESP32 (MicroPython)**  
  Reads temperature, humidity, and pressure from the BME280 over I²C and publishes the data to the Raspberry Pi via **MQTT**.

- **Raspberry Pi**  
  Runs a Mosquitto MQTT broker, stores incoming messages in an **SQLite database**, and can forward data to **Azure IoT Hub**.  
  Offline buffering ensures data is synced later if the cloud is unavailable.

## Repository structure
- ESP/ - MicroPython code for ESP32 (boot.py, main.py, secrets.py)
- RasPi/ - Python code for Raspberry Pi (app.py, config, log, db setup)
- .vscode/ - includes tasks.json to work with the esp32 and micropython.


## Usage
1. Configure `ESP/secrets.py` with Wi-Fi and MQTT details.  
2. Deploy ESP32 code using the provided VS Code tasks (`Deploy` / `Deploy & Monitor`).  
3. On the Raspberry Pi:
    - first follow: https://github.com/kapjhanze/minoriot-setup
    - then replace files with files from this repository
4. View last 5 entries of data:
    python3 show5db.py
