# Functions Of Controller

In this section we will describe what the device is capable of.

## Device Modes

Currently device support 2 modes:
- Controller
- Configuration

Mode selection happens after device is plugged to power source (or restarted).
In order to change mode you have to press device button.

### Controller Mode

This mode is responsible for animating LED-s and receiving informations from various sources.

#### How to turn this mode

This mode is selected as default (after restart / plugging in don't click button)

#### Button Functions

Button is basic way of controlling the device. Device allows only one button to be configured.
Button reacts to current device state, This mean it offers different actions if device is on or off.

Device is off:
- turn on device - this is only possible option if device is off

Device is on:
- change mode - short click (faster than 500ms)
- turn device off - normal click (500ms~2 sec)
- restart device - long press (+ 2 sec) 

** After each press device is sending update to Mqtt Broker **

#### Mqtt Functions

Mqtt allows to affect more options of device like:
- mode
- brightness
- speed of mode #TODO
- mode configuration
- state (on / off)

It is best to use some applications that allows to store prepared json in nice graphical way like:
- [MQTT Dasboard](https://play.google.com/store/apps/details?id=com.app.vetru.mqttdashboard&hl=en)

Currently tested brokers:
- [HiveMq](https://www.hivemq.com/)

##### Changing State

Sending this json will turn off / on device.

``` json
{ 
    "working": false | true
}
```

If device is off any other communicates will not be respected.

##### Changing Brightness

Brightess is responsible for how bright are the LEDs

``` json
{ 
    "brightness": 0.0-1.0
}
```

##### Changing Animation Mode & Configuration

Mode allows us to change animation. All available animations and their ids can be found in 
Available Animations Section.

``` json
{ 
    "mode": 1
    "mode_data": 
    {
        ...
    }
}
```

```mode_data``` is optional field.

##### Changing Speed

TBA.

#### Available Animations

List of available animations

##### White

In this mode device just glows white.
To turn on this mode send following json:

``` json
{ 
    "mode": 1
}
```

##### Static Color

This mode allows to change color of LED-s.

Json to enable mode and set color to red.
``` json
{ 
    "mode": 2,
    "mode_data": {
        "color": "#FF0000"
    }
}
```

If mode is enabled to change color it is enought to send just ```mode_data```.

``` json
{ 
    "mode_data": {
        "color": "#FFFF00"
    }
}
```

Alternative json to change color when mode active.
(It is not required to send all 3 fields)

``` json
{ 
    "mode_data": {
        "r": 127,
        "g": 80,
        "b": 0,
    }
}
```

If something will not be send right device will glow white.

##### RGB

In this mode nice RGB animation is performed.
Mode has no customization options.

``` 
{ 
    "mode": 3
}
```

##### Loading

In this mode leds perform similar animation to laoding.
``` json
{ 
    "mode": 4
}
```

This mode has more customization options:
- `running` - number of leds running round
- `color` or `r`, `g`, `b` combination - color of led
``` json
{ 
    "mode": 4,
    "mode_data":
    {
        "running": 5,
        "color": "#FFFF00"
        # Alternative to color
        "r": 127,
        "g": 80,
        "b": 0
    }
}
```

### Configuration Mode

This mode enables to configure basic device settings like:
- wifi info
- mqtt info
- setting number of LED
- displaying errors

#### How to turn this mode

After restart or plugging in power supply press button in range of around 2 seconds to turn on this mode.
(If device is on press device button for around 4 seconds to turn on this mode)

#### Wifi Configuration