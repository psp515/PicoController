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

##### Color

``` 
{ 
    "mode": 2
    "mode_data": {
        "color": "#FF00FF"
    }
}
```