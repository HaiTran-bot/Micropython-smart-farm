# YoloFarm - MicroPython Smart Irrigation System

A lightweight and resource-optimized smart irrigation system designed for the YoloBit platform (ESP32-based). This project features a custom, non-blocking Socket-based WebServer, RESTful APIs, and a multi-mode automation state machine implemented entirely in MicroPython and vanilla frontend technologies.

---

## Key Features

* **Custom Non-Blocking Socket Server:** Implemented directly on top of the raw TCP socket layer with low-level timeouts (0.1s) to achieve pseudo-multitasking on a single core without stalling hardware control loops.
* **Memory-Optimized RESTful API:** Employs explicit Garbage Collection (`gc.collect()`) after processing HTTP transactions to strictly prevent memory leaks under constrained RAM environments.
* **Dual Operational Mode (Hardware vs. Mock):** Includes a decoupled hardware-abstracted simulation mode (`MOCK_MODE`) enabling standalone development and testing on desktop CPython without physical sensors connected.
* **Growing Degree Days (GDD) Tracking:** Real-time localized heat unit accumulation calculation computed programmatically based on temperature and ambient light thresholds.
* **Responsive Dashboard UI:** Single Page Application (SPA) frontend that communicates asynchronously via JSON (Fetch API), featuring automatic RTC synchronization between the client browser and the ESP32 internal clock.

---

## Hardware Architecture

| Component | Functionality | Interface / Protocol |
| :--- | :--- | :--- |
| **ESP32 Core (YoloBit)** | Central Processing Unit & Wi-Fi Gateway | WROOM Architecture |
| **DHT20** | Ambient Temperature & Relative Humidity Sensing | SoftI2C Protocol |
| **Soil Moisture Sensor** | Real-time substrate volumetric water content calculation | Analog Input (ADC) |
| **Light Sensor (LUX)** | Ambient solar radiation measurement | Analog Input (ADC) |
| **LCD 1602 (PCF8574)** | Local telemetry visualization display | I2C Protocol |
| **NeoPixel RGB LED** | System operational mode visual status indicator | High-speed Single-wire PWM |
| **Dual USB Relay Module**| High-current 5V DC irrigation pump actuators | Digital Output (GPIO) |

---

## Project Structure

```text
├── boot.py              # Low-level Access Point Wi-Fi initialization
├── config.py            # Centralized threshold configurations, pins, and timing intervals
├── main.py              # Core execution loop and automated state machine logic
├── sensors.py           # Sensor telemetry acquisition and hardware abstraction layer (HAL)
├── actuators.py         # Relays and peripheral indication controller drivers
├── webserver.py         # Custom HTTP socket parsing engine and RESTful API router
├── pymakr.conf          # Pymakr plugin deployment exclusion descriptors
└── www/
    └── index.html       # Single-file HTML5/CSS3/JS AJAX responsive user interface
