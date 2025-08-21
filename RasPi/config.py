MESSAGE_TIMESPAN = 2000  # Milliseconds
SIMULATED_DATA = False
# Put your Device Connection String in here
# Example: 'HostName=iothub.azure-devices.net;DeviceId=raspberry;SharedAccessKey=VGhpcyBpcyBub3QgYWN0dWFsbHkgYSBrZXkgOik='
IOTHUB_DEVICE_CONNECTION_STRING='HostName=IoThub-aardbei.azure-devices.net;DeviceId=rasp;SharedAccessKey=9tmlCF9dIpf96rM0qi3xPS1SPjkksp9v5DzFqHrsH0k='

SETUP_COMPLETED = True

# MQTT broker info
MQTT_HOST = "pi4b-iot"   # change to your Pi IP
MQTT_PORT = 1883             # 1883 = no TLS
MQTT_TOPIC = "iot/bme280/esp32"