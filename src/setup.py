import mip

import network
import time

# Replace these with your network credentials and strt file
SSID = 'MidRouter'
PASSWORD = 'psp515!@'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print('Connecting to network...')
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(1)
        print('Connecting...')
        
print('Network config:', wlan.ifconfig())

mip.install("github:peterhinch/micropython-mqtt")