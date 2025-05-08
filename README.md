# MicroPython Exercises for IoT

- **Subject:** Fundamentals for the Internet of Things
- **Course:** Information Technology Management
- **University:** PUCPR


## Equipment
- ESP32 board
- DHT11 temperature and relative humidity sensor
- 5V relay

## Tools
- Thonny IDE
- Micropython

## Integrations
- ThingSpeak (sending data to the platform)
- IFTT (sending email)
- Discord (sending messages to the channel)

## Credentials
- Access credentials for WI-FI and external systems must be configured in the `secrets.py` file. The example file `secrets_example.py` contains the necessary variables.

## Programs

### `dht.py`:
Measures the temperature and relative humidity of the air every 1 second using the DHT sensor.

### `relay.py`:
Turns the relay on and off every 2 seconds.

### `network.py`:
Connects to a WI-FI network, accesses a web page and displays the content of this site.

### `activate_relay.py`:
Turns the relay on or off according to the temperature and relative humidity measured by the DHT11 sensor in comparison with the pre-established limits of 37°C and 70%.

### `activate_relay_and_send_alerts.py`:
- Turns the relay on or off according to the temperature and relative humidity measured by the DHT11 sensor in comparison with the pre-established limits of 37°C and 70%.
- Connects to WI-FI and sends alerts by email, Discord message, and sends the temperature and relative humidity data to the ThingSpeak platform.

### `activate_relay_by_sinusoidal_variation.py`:
- Turns the relay on or off according to the thermal sensation and relative humidity in comparison with dynamic limits, varied according to sinusoidal calculation. This application uses:

    - **ESP32** as a central controller, with Wi-Fi connection and clock via NTP to stamp each event.
    - **DHT11 sensor** to measure temperature and relative humidity.
    - **Relay** to simulate the activation of an external device whenever the climate indexes exceed the dynamic thresholds.
    - **Heat Index algorithm** to combine temperature and humidity into a single ‘thermal sensation’ metric.
    - **Sinusoidal variation** of the activation thresholds every 15 seconds, avoiding abrupt transitions and generating multiple on-off cycles.
    - **ThingSpeak** to store and visualize data in the cloud for each reading.
    - **IFTTT and Discord** to send instant alerts by email and channel message as soon as the relay changes state. 
    - **Logging system** in a local file (`log.txt`) to record all readings, threshold changes and state events, facilitating later analysis or auditing.  

    > Although this is an exercise, the smooth set-point variation pattern that is being simulated here has applications in **climate chambers** in test laboratories:
    >
    > * In industries such as pharmaceuticals and electronics, equipment is subjected to controlled temperature and humidity cycles to validate its performance and reliability under extreme conditions.
    > * Alarm and automation stress-test systems require programmed set-point changes to ensure that sensors, actuators and notifications operate correctly in rapid transitions.
    > * This technique is also used in training and demonstrations to demonstrate the robustness of a monitoring and automatic activation system.  

    <video src="./docs/activate_relay_by_sinusoidal_variation.mp4" controls></video>
