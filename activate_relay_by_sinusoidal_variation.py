# activate_relay_by_sinusoidal_variation.py
import time
import math
import machine
import dht
import network
import ntptime
import urequests
import ujson as json

# import credentials
try:
    import secrets
except ImportError:
    raise Exception("Create a secrets.py file with your credentials")

# --- Wi-Fi connection and NTP synchronization ---
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(secrets.WIFI_SSID, secrets.WIFI_PASS)
print("Connecting to Wi-Fi…")
while not wifi.isconnected():
    time.sleep(1)
print("Wi-Fi connected:", wifi.ifconfig())

try:
    ntptime.settime()
    print("NTP synchronized")
except:
    print("NTP sync failed (continuing without system time)")

# adjust for local timezone (UTC-3)
TIMEZONE_OFFSET = -3 * 3600

# --- sensor and relay setup ---
sensor = dht.DHT11(machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP))
relay_pin = machine.Pin(2, machine.Pin.OUT)
THINGSPEAK_URL = "http://api.thingspeak.com/update"

# --- sinusoidal parameters and hysteresis ---
CYCLE_PERIOD      = 30.0   # cycle period in seconds

HI_BASE           = 38.0   # base Heat Index (°C)
HI_AMPLITUDE      = 10.0    # Heat Index amplitude (°C)
HI_HYSTERESIS     = 2.0    # Heat Index hysteresis (°C)

HUM_BASE          = 65.0   # base humidity (%)
HUM_AMPLITUDE     = 40.0   # humidity amplitude (%)
HUM_HYSTERESIS    = 5.0    # humidity hysteresis (%)

VARIATION_SPEED = 2.0

last_state         = 0
last_limit_update  = 0

# --- utility functions ---
def log_event(message):
    """Append a timestamp and message to log.txt."""
    try:
        tm = time.localtime(time.time() + TIMEZONE_OFFSET)
        timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            tm[0], tm[1], tm[2], tm[3], tm[4], tm[5]
        )
        with open("log.txt", "a") as f:
            f.write(f"{timestamp} - {message}\n")
    except Exception as e:
        print("Log error:", e)

def heat_index(temp_c, rel_humidity):
    """Calculate NOAA Heat Index (°C)."""
    T = temp_c
    RH = rel_humidity
    T2 = T * T
    RH2 = RH * RH
    return (
        -8.784695
        + 1.61139411 * T
        + 2.338549   * RH
        - 0.14611605 * T * RH
        - 0.012308094 * T2
        - 0.016424828 * RH2
        + 0.002211732 * T2 * RH
        + 0.00072546  * T * RH2
        - 0.000003582 * T2 * RH2
    )

def send_ifttt_alert(temp_c, humidity, state):
    """Trigger IFTTT event with temperature, humidity, and relay state."""
    url = (
        "https://maker.ifttt.com/trigger/{event}/with/key/{key}"
        "?value1={t}&value2={h}&value3={s}"
    ).format(
        event=secrets.IFTTT_EVENT_NAME,
        key=secrets.IFTTT_KEY,
        t=temp_c,
        h=humidity,
        s="ON" if state else "OFF"
    )
    try:
        urequests.get(url).close()
        log_event("IFTTT alert sent")
    except Exception as e:
        log_event(f"IFTTT error: {e}")

def send_discord_alert(temp_c, humidity, state):
    """
    Send a message to the Discord channel via Webhook,
    using 'json=' when possible and falling back to 'data+'headers' if necessary.
    Also prints the payload and HTTP status for debugging.
    """
    # Alert message
    onOf = 'ON' if state else 'OFF'
    msg = "Relay Alert! {} :: Temperature: {} C  Humidity: {} %".format(onOf, temp_c, humidity)
    
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

# --- main loop ---
while True:
    current_time = time.time()

    # 1) Recalculate limits every 15 seconds
    if current_time - last_limit_update >= 15:
        angle  = 2 * math.pi * ((current_time % CYCLE_PERIOD) / CYCLE_PERIOD) * VARIATION_SPEED
        hi_on  = HI_BASE + HI_AMPLITUDE * math.sin(angle)
        hi_off = hi_on - HI_HYSTERESIS
        hum_on = HUM_BASE + HUM_AMPLITUDE * math.sin(angle)
        hum_off= hum_on - HUM_HYSTERESIS

        limits_msg = (
            f"New limits: HI_ON={hi_on:.1f} HI_OFF={hi_off:.1f} | "
            f"HUM_ON={hum_on:.1f} HUM_OFF={hum_off:.1f}"
        )
        print(limits_msg)
        log_event(limits_msg)
        last_limit_update = current_time

    # 2) Read sensor and compute Heat Index
    sensor.measure()
    temp_c    = sensor.temperature()
    humidity  = sensor.humidity()
    hi_value  = heat_index(temp_c, humidity)

    read_msg = f"Reading: T={temp_c}°C  RH={humidity}%  HI={hi_value:.1f}°C"
    print(read_msg)
    log_event(read_msg)

    # 3) Dual hysteresis control for Heat Index and humidity
    if last_state == 0 and (hi_value >= hi_on or humidity >= hum_on):
        relay_pin.on()
        new_state = 1
    elif last_state == 1 and (hi_value <= hi_off and humidity <= hum_off):
        relay_pin.off()
        new_state = 0
    else:
        new_state = last_state

    # 4) Send data to ThingSpeak
    try:
        urequests.get(
            f"{THINGSPEAK_URL}"
            f"?api_key={secrets.THINGSPEAK_API_KEY}"
            f"&field1={temp_c}&field2={humidity}&field3={new_state}"
        ).close()
        log_event("ThingSpeak update sent")
    except Exception as e:
        log_event(f"ThingSpeak error: {e}")

    # 5) Fire alerts on state transition
    if new_state != last_state:
        state_str = "ON" if new_state else "OFF"
        print(f"→ Relay {state_str}")
        log_event(f"Relay {state_str}")
        send_ifttt_alert(temp_c, humidity, new_state)
        send_discord_alert(temp_c, humidity, new_state)
        last_state = new_state

    # 6) Pause for 15 seconds
    time.sleep(15)
