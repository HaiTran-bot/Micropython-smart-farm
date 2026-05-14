# =============================================================
# YoloFarm — actuators.py
# Actuator control module (Pumps, RGB LED)
# =============================================================

from config import (
    PIN_PUMP1, PIN_PUMP2, PIN_RGB, RGB_NUM,
    COLOR_RED, COLOR_GREEN, COLOR_YELLOW, COLOR_OFF,
    MODE_MANUAL, MODE_AUTO_SENSOR, MODE_AUTO_SCHEDULE,
    MOCK_MODE
)

if not MOCK_MODE:
    from homebit3_rgbled import RGBLed
    from yolobit import *


class ActuatorManager:
    """Quản lý điều khiển bơm và đèn RGB."""

    def __init__(self):
        if not MOCK_MODE:
            self.rgb = RGBLed(pin0.pin, RGB_NUM)

        self.pump1_state = 0   # 0 = OFF, 1 = ON
        self.pump2_state = 0

        print("[actuators] ActuatorManager initialized (MOCK_MODE=" + str(MOCK_MODE) + ")")

    # ---- Pump Control ----

    def set_pump1(self, state):
        """Bật/tắt Pump 1. state: 0 hoặc 1."""
        self.pump1_state = state
        
        if MOCK_MODE:
            print("[actuators] Pump 1 -> " + ("ON" if state else "OFF"))
        else:
            pin10.write_digital(state)

    def set_pump2(self, state):
        """Bật/tắt Pump 2 / Light. state: 0 hoặc 1."""
        self.pump2_state = state
        
        if MOCK_MODE:
            print("[actuators] Pump 2 -> " + ("ON" if state else "OFF"))
        else:
            pin13.write_digital(state)

    # ---- RGB LED ----

    def set_mode_led(self, mode):
        """Đổi màu RGB LED theo MODE hiện tại."""
        if mode == MODE_MANUAL:
            color = COLOR_RED
        elif mode == MODE_AUTO_SENSOR:
            color = COLOR_GREEN
        elif mode == MODE_AUTO_SCHEDULE:
            color = COLOR_YELLOW
        else:
            color = COLOR_OFF

        if MOCK_MODE:
            print("[actuators] RGB LED -> " + str(color))
        else:
            for i in range(RGB_NUM):
                self.rgb.show(i, color)

    # ---- Status ----

    def get_status(self):
        """Trả về trạng thái hiện tại của các actuator."""
        return {
            "pump1": self.pump1_state,
            "pump2": self.pump2_state,
        }
