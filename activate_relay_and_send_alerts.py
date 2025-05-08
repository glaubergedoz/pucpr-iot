import time
import machine
import dht
import network
import urequests
import ujson as json

# import credentials
try:
    import secrets
except ImportError:
    raise Exception("Create a secrets.py file with your credentials")

# --- alert functions ---

def send_ifttt_alert(temp_c, humidity):
    """Trigger the IFTTT event (which will send an email)."""
    url = (
        "https://maker.ifttt.com/trigger/{event}/with/key/{key}"
        "?value1={t}&value2={h}"
    ).format(
        event=secrets.IFTTT_EVENT_NAME,
        key=secrets.IFTTT_KEY,
        t=temp_c,
        h=humidity
    )
    try:
        resp = urequests.get(url)
        resp.close()
        print("→ IFTTT OK")
    except Exception as e:
        print("✖ IFTTT Error:", e)

def send_discord_alert(temp_c, humidity):
    """
    Send a message to the Discord channel via Webhook,
    using 'json=' when possible and falling back to 'data+'headers' if necessary.
    Also prints the payload and HTTP status for debugging.
    """
    # Alert message
    msg = "Alert! Temperature: {} C  Humidity: {} %".format(temp_c, humidity)
    
    headers = {"Content-Type": "application/json"}
    
    try:
        # Try using json parameter (automatic and cleaner)
        resp = urequests.post(
            secrets.DISCORD_WEBHOOK_URL,
            json={"content": msg}
        )
    except TypeError:
        # If json= is not supported, manually assemble the JSON
        import ujson
        payload = ujson.dumps({"content": msg})
        resp = urequests.post(
            secrets.DISCORD_WEBHOOK_URL,
            data=payload,
            headers=headers
        )
    
    # Print response status and body to check for errors
    print("Discord status:", resp.status_code, resp.text)
    resp.close()



# --- Wi-Fi setup ---

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(secrets.WIFI_SSID, secrets.WIFI_PASS)
print("Connecting to Wi-Fi…")
while not wifi.isconnected():
    time.sleep(1)
print("Wi-Fi connected:", wifi.ifconfig())

# --- sensor and relay setup ---

sensor = dht.DHT11(machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP))
relay_pin = machine.Pin(2, machine.Pin.OUT)

TEMP_THRESHOLD     = 37   # °C
HUMIDITY_THRESHOLD = 70   # %
THINGSPEAK_URL     = "http://api.thingspeak.com/update"

last_state = 0

# --- main loop ---

while True:
    try:
        # 1) read sensor
        sensor.measure()
        temp_c = sensor.temperature()
        humidity = sensor.humidity()
        print(f"T: {temp_c} °C  H: {humidity} %")

        # 2) determine relay state
        if temp_c > TEMP_THRESHOLD or humidity > HUMIDITY_THRESHOLD:
            relay_pin.on()
            current_state = 1
        else:
            relay_pin.off()
            current_state = 0

        # 3) send data to ThingSpeak
        url = (
            f"{THINGSPEAK_URL}"
            f"?api_key={secrets.THINGSPEAK_API_KEY}"
            f"&field1={temp_c}"
            f"&field2={humidity}"
            f"&field3={current_state}"
        )
        try:
            resp = urequests.get(url)
            resp.close()
        except:
            pass

        # 4) if relay just turned on, fire alerts
        if current_state == 1 and last_state == 0:
            send_ifttt_alert(temp_c, humidity)
            send_discord_alert(temp_c, humidity)

        last_state = current_state

    except Exception as e:
        print("GENERAL ERROR:", e)

    # Free ThingSpeak account requires at least 15s between updates
    time.sleep(15)

