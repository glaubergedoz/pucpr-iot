import dht
import machine
import time

d=dht.DHT11(machine.Pin(4))

while True:
    d.measure()
    print("Temperature={} Humidity={}".format(d.temperature(), d.humidity()))
    time.sleep(1)
