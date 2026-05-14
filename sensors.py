# =============================================================
# YoloFarm — sensors.py
# Sensor reading module
# =============================================================

import random
from config import MOCK_MODE

if not MOCK_MODE:
    from homebit3_dht20 import DHT20
    from homebit3_lcd1602 import LCD1602
    from yolobit import *


class SensorManager:
    """Quản lý đọc cảm biến và cập nhật LCD."""

    def __init__(self):
        if not MOCK_MODE:
            self.dht20 = DHT20()
            self.lcd = LCD1602()

        # Dữ liệu cảm biến mới nhất
        self.data = {
            "temperature": 0,
            "humidity": 0,
            "soil": 0,
            "light": 0,
        }
        print("[sensors] SensorManager initialized (MOCK_MODE=" + str(MOCK_MODE) + ")")

    def read_all(self):
        """Đọc tất cả cảm biến và trả về dict kết quả."""

        if MOCK_MODE:
            # --- START MOCK DATA ---
            temperature = round(random.uniform(25, 35), 1)   # °C
            humidity    = round(random.uniform(60, 90), 1)   # %
            soil        = round(random.uniform(30, 80), 1)   # %
            light       = random.randint(400, 3000)          # LUX
            # --- END MOCK DATA ---
        else:
            self.dht20.read_dht20()
            temperature = self.dht20.dht20_temperature()
            humidity    = self.dht20.dht20_humidity()
            soil_raw    = pin1.read_analog()
            soil        = translate(soil_raw, 0, 4096, 0, 100)
            light       = pin2.read_analog()

        self.data["temperature"] = temperature
        self.data["humidity"]    = humidity
        self.data["soil"]        = soil
        self.data["light"]       = light

        return self.data

    def update_lcd(self, data):
        """Hiển thị dữ liệu cảm biến lên LCD 1602."""

        # 1. Định dạng từng cụm thông số theo đúng chữ trong ảnh
        temp_str = "RT:{:.1f}*C".format(data["temperature"])
        humid_str = "RH:{:.0f}%".format(data["humidity"])
        
        light_str = "LUX:{}".format(data["light"])
        soil_str = "SM:{:.0f}%".format(data["soil"])

        # 2. Ghép chuỗi: Ép cụm bên phải (RH, SM) luôn bắt đầu từ ô số 10
        # bằng cách chèn số lượng khoảng trắng (space) tương ứng vào giữa
        line1 = temp_str + " " * (10 - len(temp_str)) + humid_str
        line2 = light_str + " " * (10 - len(light_str)) + soil_str

        if MOCK_MODE:
            # Mock: In ra console thay cho LCD
            print("[LCD] " + line1 + " | " + line2)
        else:
            self.lcd.move_to(0, 0)
            # (chuỗi + 16 khoảng trắng)[:16] giúp ép chuỗi luôn dài đúng 16 ký tự
            # để xoá sạch các ký tự cũ (rác) còn sót lại trên màn hình
            self.lcd.putstr((line1 + " " * 16)[:16])
            self.lcd.move_to(0, 1)
            self.lcd.putstr((line2 + " " * 16)[:16])
    def get_latest(self):
        """Trả về dữ liệu cảm biến mới nhất (không đọc lại)."""
        return self.data
