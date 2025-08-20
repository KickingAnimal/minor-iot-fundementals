# Minor IoT - Setup

Use the Azure IoT environment to receive temperature and humidity measurements from a BME280 sensor connected to a Raspberry Pi device. All written in Python and easy to use. Many thanks to Jorian Woltjer en Aji Rajadurai (SCMI) for writing this new script! 

## Example

This is an example of how the output should look like when the BME280 sensor is connected properly and when the Raspberry Pi is successfully connected to the Azure IoT Hub.

![A terminal showing colored output from running `./app.py`](https://user-images.githubusercontent.com/53057598/196724015-120a2c0f-39d6-4dae-b415-3de2b44bb55f.png)

## Usage

```Shell
usage: app.py [-h] [-s] [-t TIME] [-n] [connection]

positional arguments:
  connection            Device Connection String from Azure

optional arguments:
  -h, --help            show this help message and exit
  -s, --simulated       Simulates temperature and humidity data from the BME280 with random values
  -t TIME, --time TIME  Time in between messages sent to IoT Hub, in milliseconds (default: 2000ms)
  -n, --no-send         Disable sending data to IoTHub, only print to console
```

## Setup

### Step 1: Install Raspberry Pi OS

Download and install the latest version of [Raspberry Pi Imager](https://www.raspberrypi.com/software/) on your host machine. 
Then choose the Raspberry Pi OS that best fits your needs:

* For the easiest development experience, install Raspberry Pi OS **Desktop**
* For the best performence and low disk space, install Raspberry Pi OS **Lite** (no GUI)

Before installing, make sure you set up the **SSH** credentials. You can use a public key to easily connect from your specific device, 
or set a password to log in from anywhere. 

Also make sure to set the Wi-Fi settings for the Pi to be able to connect the a network, and access it later via SSH. If you can, we recommend starting a **hotspot** on your laptop or phone. This way you can see what IP address connects and easily find the IP address without needing an extra monitor. 

When the image is fully written to the Raspberry Pi, you can connect the it via SSH in the next step. 

### Step 2: Connect via SSH

* If you have set up the Wi-Fi while installing, create the hotspot or use the same Wi-Fi network to find the IP address. 
* If you haven't set up Wi-Fi, you can also use an extra monitor to see the GUI of Raspberry Pi OS. Note that this only works on Raspberry Pi OS **Desktop**. 

> **Note**: If you think you messed something up, you can always write the image again as in step 1, and change any settings

![Screenshot of the Hotspot feature in Windows Settings, showing a table with the IP address](https://user-images.githubusercontent.com/26067369/196721962-c6a9f137-a769-4a18-be8b-530a472e7a49.png)

When you have an IP address, you can use the SSH command to connect to it, using the credentials you set in step 1. In this case the username is to `pi`, and the password to `raspberry`, so the command would become the following:

```Shell
ssh pi@192.168.137.216
Password: raspberry
```

Once you're connected to the Pi via SSH, you can begin to install this repository in the next step.

### Step 3: Install this repository

To get everything up and running on the Raspberry PI, you can use the following commands on the Pi to install this repository:

```Shell
git clone https://github.com/kapjhanze/minoriot-setup.git && cd minoriot-setup
sudo bash setup.sh
```

This [`setup.sh`](setup.sh) script should install all the necessary dependencies and settings. Reboot after the installation to make sure everything is reloaded. 

### Step 4: Get the Device Connection String

To receive data from your device in the Azure environment you have to connect it with a secret string. 

Log in to the [Azure Portal](https://portal.azure.com/) and navigate to the IoT Hub you created. Then navigate to the **Devices** tab on the left and click on the device you created. From there you can copy the **Primary Connection String**. It should look something like this: 

```
HostName=iothub.azure-devices.net;DeviceId=raspberry;SharedAccessKey=VGhpcyBpcyBub3QgYWN0dWFsbHkgYSBrZXkgOik=
```

The Azure Connection String can be added to the [`config.py`](config.py) file or can be used as an argument when running `python3 app.py`.

### Step 5: Connecting the BME280 sensor to the Raspberry Pi

By default, the `app.py` script will not read any data from a connected BME280, instead it will simulate values by randomly generating them. You can edit the [`config.py`](config.py) file to set `SIMULATED_DATA = False`. This will then look for a BME280 sensor when you start the script. 

The BME280 sensor will likely have four pins labeled `VIN` (5V), `GND`, `SCL` (Serial Clock) and `SDA` (Serial Data). Connect these to the corresponding pins on the Raspberry Pi:

* [Pin Layout - Raspberry Pi 3](https://s3.amazonaws.com/youngwonks/Blogs/GPIO_diagram.jpg)
* [Pin Layout - Raspberry Pi 4](https://www.etechnophiles.com/wp-content/uploads/2021/01/R-Pi-4-GPIO-Pinout.jpg)

After the BME280 sensor is connected, you should be able to see the address `76` using the tool install when you ran `setup.sh`:

```Shell
i2cdetect -y 1
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- 76 --
```

### Step 6: Test using Azure IoT Explorer

To test if the data is sent to the Azure IoT Hub, you can use a program called Azure IoT Explorer. 

Azure IoT Hub can be downloaded on your host from the [Azure IoT Explorer GitHub repository](https://github.com/Azure/azure-iot-explorer/releases)

After installing the IoT Explorer you can add connection by pressing **Add connection**. Here you can add a connection string.

To get an connection string, you need to login to the [Azure Portal](https://portal.azure.com/) and navigate to the IoT Hub you created. Then navigate to the **Shared access policies** tab on the left. From there you can click on the **iothubowner** policy, and can copy its **Primary connection string**. 

![A screenshot of the Shared access policies, show a list including the iothubowner policy](https://user-images.githubusercontent.com/53057598/196728717-de1de334-6265-4f0a-87d8-31fc6cff980d.png)

After adding the connection string on the IoT Explorer it will list the devices which are connected to the IoT Hub. You should see the Raspberry Pi here, and you can click on it to see more information. Finally you can visit the **Telemetry** tab and click **Start** button to start listening for any incoming message from the device. 

If the `app.py` script is running, and successfully connects to the IoTHub, you should now see JSON formatted message come in every once in a while:

![A screenshot of Azure IoT Explorer showing two sample JSON messages from the Pi](https://user-images.githubusercontent.com/53057598/196733101-78f0756c-1211-43fd-8029-7910853cb0bd.png)

## Troubleshooting

* [Alternative i2c setup](https://www.raspberrypi.com/documentation/computers/configuration.html)
