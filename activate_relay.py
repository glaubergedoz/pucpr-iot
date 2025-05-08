import machine
import time
import dht

# --- PIN CONFIGURATION ---
pin_dht  = machine.Pin(4,  machine.Pin.IN,  machine.Pin.PULL_UP)   # DHT11 on GPIO4
pin_rele = machine.Pin(2,  machine.Pin.OUT)                       # Relay on GPIO2

sensor = dht.DHT11(pin_dht)

# pin_rele.on() → turns off
# pin_rele.off() → turns on

# --- LIMIT PARAMETERS ---
TEMP_LIMIT = 37   # °C
HUMID_LIMIT = 70   # %

while True:
    try:
        # take the measurement
        sensor.measure()
        temp = sensor.temperature()
        hum  = sensor.humidity()
        print("Temperature: {} °C | Humidity: {} %".format(temp, hum))
        
        # trigger logic
        if temp > TEMP_LIMIT or hum > HUMID_LIMIT:
            pin_rele.on()   # activate the relay
            print("→ Relay ON!")
        else:
            pin_rele.off()  # turn off the relay
            print("→ Relay OFF.")
            
    except OSError as e:
        print("Error reading DHT11:", e)
    
    # waits 1 s before next reading
    time.sleep(1)

