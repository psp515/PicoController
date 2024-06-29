# Configuration

## Setup Device

Raspberry pi pico W have to be configuret with python ```.u2f``` file.
In order to prepare device follow [this tutorial from Rapberry Pi Documentation](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html)

## Transfer Files

Eeasies way of transferrin files is by using [Thonny](https://thonny.org/) you can find how transfer files in this [youtube short](https://www.youtube.com/shorts/QV9Y7B0CG1k)

Only contents of src folder should be copied to raspberry pi pico.
(dont upload src folder you have to upload contents of folder to pico so main.py is in root folder)

## Prepare libaries

We have to install following libraries to device:
- [mqtt-as]()

### Using Thonny Script

In thony open ```setup.py``` file, then fill your wifi credentials and after that run script and wait for libraries to install .

### Copying files manually

In ```src``` folder create folder named ```lib``` and:
- copy [mqtt-as.py](https://github.com/peterhinch/micropython-mqtt/blob/master/mqtt_as/mqtt_as.py) file to it (also you can create this file and copy contents)

Then upload this folder like in previous Transfering files step.

## Wiring Example 

Schema is example schema and can be configured.

![image](https://github.com/psp515/PicoController/assets/69080157/e89f11bb-18a2-498d-9ba6-92698c849342)

Configurables can be found in ```app_settings.json```:
- Neopixel strip pin - ```strip:pin``` - default pin ```15```
- Button stip pin - ```button:pin``` - default pin ```14```

This should not be changed when device is working.

## Web Server Configuration

Web server is mode of device that allows configuring device without connecting to computer.

Configurables can be found in ```app_settings.json``` in section ```webserver``` :
- ```ssid``` - ssid under what you will be able to connect with raspberry pi pico
- ```password``` - password required for connecting with raspberry pi pico

More about web server can be found in its section in [usage documentation](https://github.com/psp515/PicoController/tree/main/docs/usage).

## Example 3D Project

Be aware that this is example project and may not be suitable for you.

[Pico Controller on Thingiverse](https://www.thingiverse.com/thing:6678379)

### 0.0.1

Required Parts:
- Raspberry Pi Pico W
- Wsb 2812b LEDs
- 5V Power Supply
- 5V dc socket with wire 
- 1 button
- some wires 

Optional Parts
- 4 M1 Screws
- Threaded terminal strip 1,5mm2 LPA12-1.5

PHOTO

Knwon Problems:
- it is hard to open casing
- it is difficult to close casing ig you have hard cables

## Startup

If all steps are completed successfully device will start working after plugging in power supply.
(If device is not configured device button will be working).

[Now check out wahat device is capable of.](https://github.com/psp515/PicoController/tree/main/docs/usage)
