# =============================================================
# YoloFarm — main.py
# Main application: Webserver + State Machine loop
# =============================================================

import time
from config import (
    SERVER_PORT,
    SENSOR_INTERVAL, CONTROL_INTERVAL, GDD_INTERVAL,
    MODE_MANUAL, MODE_AUTO_SENSOR, MODE_AUTO_SCHEDULE,
    SOIL_LOW, SOIL_HIGH, LUX_LOW, LUX_GDD,
)
from sensors import SensorManager
from actuators import ActuatorManager
from webserver import WebServer


# =============================================================
# Global State
# =============================================================
current_mode = MODE_MANUAL   # 0=Manual, 1=AutoSensor, 2=AutoSchedule
gdd_counter  = 0.0           # Growing Degree Days


def millis():
    """Trả về thời gian hiện tại tính bằng milliseconds."""
    return int(time.time() * 1000)


# =============================================================
# API Callbacks (được gọi bởi WebServer)
# =============================================================

def api_get_data():
    """Callback cho GET /api/data → trả về toàn bộ trạng thái."""
    from config import MOCK_MODE
    sensor_data = sensors.get_latest()
    actuator_status = actuators.get_status()
    return {
        "temperature": sensor_data["temperature"],
        "humidity":    sensor_data["humidity"],
        "soil":        sensor_data["soil"],
        "light":       sensor_data["light"],
        "gdd":         round(gdd_counter, 2),
        "mode":        current_mode,
        "pump1":       actuator_status["pump1"],
        "pump2":       actuator_status["pump2"],
        "is_mock":     MOCK_MODE,
    }


def api_set_mode(mode):
    """Callback cho POST /api/mode → đổi chế độ."""
    global current_mode
    if mode in (MODE_MANUAL, MODE_AUTO_SENSOR, MODE_AUTO_SCHEDULE):
        current_mode = mode
        actuators.set_mode_led(mode)
        print("[main] Mode changed -> {}".format(mode))
        # Khi chuyển sang Auto, tắt cả 2 bơm (reset)
        if mode != MODE_MANUAL:
            actuators.set_pump1(0)
            actuators.set_pump2(0)


def api_set_pump(pump, state):
    """Callback cho POST /api/pump → điều khiển bơm thủ công."""
    if current_mode != MODE_MANUAL:
        return False  # Chỉ cho phép ở MODE 0
    if pump == 1:
        actuators.set_pump1(state)
    elif pump == 2:
        actuators.set_pump2(state)
    return True

def api_sync_time(data):
    """Callback cho POST /api/time -> đồng bộ RTC của ESP32."""
    try:
        y = data.get("year", 2026)
        m = data.get("month", 1)
        d = data.get("day", 1)
        wd = data.get("weekday", 0)
        h = data.get("hour", 0)
        minute = data.get("minute", 0)
        s = data.get("second", 0)
        
        from config import MOCK_MODE
        if MOCK_MODE:
            print("[main] (MOCK) RTC Sync -> {:02d}:{:02d}:{:02d} {}/{}/{}".format(h, minute, s, d, m, y))
        else:
            import machine
            rtc = machine.RTC()
            rtc.datetime((y, m, d, wd, h, minute, s, 0))
            print("[main] (REAL) RTC Sync -> {:02d}:{:02d}:{:02d} {}/{}/{}".format(h, minute, s, d, m, y))
    except Exception as e:
        print("[main] Lỗi đồng bộ thời gian:", e)


# =============================================================
# Auto Control Logic
# =============================================================

def auto_sensor_control(data):
    """MODE 1: Tự động dựa trên ngưỡng cảm biến."""
    sm = data["soil"]
    lux = data["light"]

    # Bật bơm nếu đất khô VÀ ánh sáng yếu
    if sm < SOIL_LOW and lux < LUX_LOW:
        actuators.set_pump1(1)
        print("[auto] Soil dry + Low light -> Pump 1 ON")
    # Tắt bơm nếu đất đã đủ ẩm
    elif sm > SOIL_HIGH:
        actuators.set_pump1(0)
        print("[auto] Soil wet enough -> Pump 1 OFF")


_last_schedule_key = None  # Theo dõi schedule đã thực thi để tránh lặp

def auto_schedule_control():
    """MODE 2: Tự động theo lịch."""
    global _last_schedule_key
    t = time.localtime()
    hour = t[3]
    minute = t[4]
    current_key = hour * 60 + minute  # Chuyển thành phút trong ngày

    from config import SCHEDULE_ON_OFF
    for h, m, state in SCHEDULE_ON_OFF:
        target_key = h * 60 + m
        if current_key == target_key and _last_schedule_key != target_key:
            # Chỉ thực thi 1 lần trong phút đó (tránh trigger lặp mỗi 10s)
            _last_schedule_key = target_key
            actuators.set_pump2(state)
            print("[schedule] {}:{:02d} -> Pump 2 {}".format(h, m, "ON" if state else "OFF"))
            break

    # Reset tracker khi đã qua phút schedule (cho phép trigger lại ngày hôm sau)
    if _last_schedule_key is not None:
        if current_key != _last_schedule_key:
            _last_schedule_key = None


def update_gdd(data):
    """Cập nhật Growing Degree Days."""
    global gdd_counter
    if data["light"] >= LUX_GDD:
        # Tăng GDD — mỗi phút tương đương 1/1440 ngày
        gdd_counter += data["temperature"] / 1440.0
        print("[gdd] GDD = {:.2f}".format(gdd_counter))


# =============================================================
# Main Entry Point
# =============================================================

def main():
    global sensors, actuators

    print("=" * 50)
    print("   YoloFarm Local Webserver — Starting...")
    print("=" * 50)

    # Khởi tạo modules
    sensors   = SensorManager()
    actuators = ActuatorManager()
    server    = WebServer(port=SERVER_PORT)

    # Gắn callbacks cho webserver
    server.on_get_data = api_get_data
    server.on_set_mode = api_set_mode
    server.on_set_pump = api_set_pump
    server.on_sync_time = api_sync_time

    # Khởi động server
    server.start()

    # Đặt LED mặc định cho MODE ban đầu
    actuators.set_mode_led(current_mode)

    # Đọc sensor lần đầu
    data = sensors.read_all()
    sensors.update_lcd(data)

    # Timestamps cho non-blocking intervals
    last_sensor  = millis()
    last_control = millis()
    last_gdd     = millis()

    print("[main] Entering main loop... (Ctrl+C to stop)")
    print("[main] Open http://localhost:{} in your browser".format(SERVER_PORT))
    print()

    try:
        while True:
            now = millis()

            # 1. Poll webserver (non-blocking)
            server.poll()

            # 2. Đọc cảm biến theo chu kỳ
            if now - last_sensor >= SENSOR_INTERVAL:
                last_sensor = now
                data = sensors.read_all()
                sensors.update_lcd(data)

            # 3. Auto-control theo chu kỳ
            if now - last_control >= CONTROL_INTERVAL:
                last_control = now
                if current_mode == MODE_AUTO_SENSOR:
                    auto_sensor_control(sensors.get_latest())
                elif current_mode == MODE_AUTO_SCHEDULE:
                    auto_schedule_control()

            # 4. GDD theo chu kỳ
            if now - last_gdd >= GDD_INTERVAL:
                last_gdd = now
                update_gdd(sensors.get_latest())

            # 5. Sleep nhỏ để không chiếm CPU 100%
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n[main] Shutting down...")
        server.stop()
        print("[main] Goodbye!")


# Chạy chương trình
if __name__ == "__main__":
    main()
