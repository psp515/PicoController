# Documentation

## General informations


## Infulecing device behaviour

### Button

### MQTT

Configuring mqtt allows to remotely control device.

Currently tested brokers:
- [HiveMq](https://www.hivemq.com/)

#### Communicates

#### On / Off

Sending this json will turn off / on device.
If device is off any other communicates will not be respected.

``` 
{ 
    "working": false | true
}
```

#### Brightess

Brightess is responsible for how bright are the LEDs

``` 
{ 
    "brightness": 0.0-1.0
}
```

#### Mode

Mode is curent lightning style by device.

##### White

``` 
{ 
    "mode": 1
}
```

##### Static Color

Json to enable mode and set color to magenta.
``` 
{ 
    "mode": 2,
    "mode_data": {
        "color": "#FF00FF"
    }
}
```

Json to change color when mode active.

``` 
{ 
    "mode_data": {
        "color": "#FFFF00"
    }
}
```

Alternative json to change color when mode active.

``` 
{ 
    "mode_data": {
        "r": 127,
        "g": 80,
        "b": 0,
    }
}
```

##### RGB

Json to enable mode..
``` 
{ 
    "mode": 3
}
```

##### Loading

Json to enable mode.
``` 
{ 
    "mode": 4
}
```

Full management json.
``` 
{ 
    "mode": 4,
    "mode_data":
    {
        "running": 5 # Number of running leds,
        "color": "#FFFF00"
        # Alternative
        "r": 127,
        "g": 80,
        "b": 0
    }
}
```