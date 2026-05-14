# =============================================================
# YoloFarm — boot.py
# Khởi chạy một lần khi cấp nguồn: Thiết lập WiFi Access Point
# =============================================================

from config import MOCK_MODE, AP_SSID, AP_PASSWORD

if not MOCK_MODE:
    import network
    import time

    def setup_ap():
        print("=" * 40)
        print("  Khoi tao WiFi Access Point  ")
        print("=" * 40)

        # 1. Tat giao dien ket noi WiFi ngoai (Station Mode)
        sta = network.WLAN(network.STA_IF)
        sta.active(False)

        # 2. Bat giao dien phat WiFi (AP Mode)
        ap = network.WLAN(network.AP_IF)
        ap.active(True)

        # 3. Cau hinh SSID va Mat khau (authmode=3 = WPA2-PSK)
        try:
            ap.config(essid=AP_SSID, password=AP_PASSWORD, authmode=3)
        except Exception:
            ap.config(essid=AP_SSID, password=AP_PASSWORD)

        # Cho AP khoi dong hoan toan
        time.sleep(2)

        # 4. In thong tin
        try:
            ip_info = ap.ifconfig()
            the_ip = ip_info[0]
        except Exception:
            the_ip = "192.168.4.1"

        print("YoloFarm AP da san sang!")
        print("SSID:", AP_SSID)
        print("Pass:", AP_PASSWORD)
        print("IP:  ", the_ip)
        print("=" * 40)

    try:
        setup_ap()
    except Exception as e:
        print("Loi cau hinh AP:", e)
else:
    print("[boot] MOCK_MODE=True -> Bo qua cau hinh WiFi AP")
