# =============================================================
# YoloFarm — config.py
# Centralized configuration constants
# =============================================================

# ----- System Mode -----
MOCK_MODE = False     # True: Giải lập dữ liệu (Test PC), False: Chạy thật trên ESP32

# ----- WiFi Access Point -----
AP_SSID     = "YoloFarm"
AP_PASSWORD  = "12345678"

# ----- Web Server -----
SERVER_PORT = 8080 if MOCK_MODE else 80  # PC dùng 8080 (port 80 cần admin), ESP32 dùng 80

# ----- Pin Assignments -----
PIN_SOIL    = 1      # pin1 — Soil Moisture (analog)
PIN_LIGHT   = 2      # pin2 — Light / LUX (analog)
PIN_PUMP1   = 10     # pin10 — Pump 1 (digital out)
PIN_PUMP2   = 13     # pin13 — Pump 2 / Light (digital out)
PIN_RGB     = 0      # pin0 — NeoPixel RGB LED
RGB_NUM     = 4      # Number of NeoPixel LEDs

# ----- Intervals (milliseconds) -----
SENSOR_INTERVAL   = 5000    # Read sensors every 5 s
CONTROL_INTERVAL  = 10000   # Auto-control check every 10 s
GDD_INTERVAL      = 60000   # GDD update every 60 s

# ----- Mode Definitions -----
MODE_MANUAL        = 0
MODE_AUTO_SENSOR   = 1
MODE_AUTO_SCHEDULE = 2

# ----- Threshold Values -----
SOIL_LOW   = 45     # Soil Moisture < 45 → too dry
SOIL_HIGH  = 80     # Soil Moisture > 80 → wet enough
LUX_LOW    = 600    # LUX < 600  → low light
LUX_GDD    = 2000   # LUX >= 2000 → count toward GDD

# ----- MODE 2 Schedule (hour, minute) -----
SCHEDULE_ON_OFF = [
    (8,  0,  1),   # 08:00 → ON
    (8,  15, 0),   # 08:15 → OFF
    (12, 0,  1),   # 12:00 → ON
    (12, 10, 0),   # 12:10 → OFF
    (17, 0,  1),   # 17:00 → ON
    (17, 15, 0),   # 17:15 → OFF
]

# ----- RGB Colors (R, G, B) -----
COLOR_RED    = (255, 0, 0)      # MODE 0 — Manual
COLOR_GREEN  = (0, 255, 0)      # MODE 1 — Auto-Sensor
COLOR_YELLOW = (255, 255, 0)    # MODE 2 — Auto-Schedule
COLOR_OFF    = (0, 0, 0)
