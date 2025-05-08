try:
    import secrets
except ImportError:
    raise Exception("secrets.py not found")

def connect(ssid, password):
    import network
    import time
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(ssid, password)
    for t in range(50):
        if station.isconnected():
            break
        time.sleep(0.1)
    return station

import urequests
print("Connecting...")
station = connect(secrets.WIFI_SSID, secrets.WIFI_PASS)
if not station.isconnected():
    print("Not connected!")
else:
    print("Connected!")
    print("Accessing the page...")
    response = urequests.get("https://www.ppgia.pucpr.br")
    print("Page accessed!")
    print(response.text)
    station.disconnect()


