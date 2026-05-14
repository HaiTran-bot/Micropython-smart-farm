# =============================================================
# YoloFarm — webserver.py
# Lightweight non-blocking HTTP server
# Compatible with both MicroPython (ESP32) and CPython (desktop)
# =============================================================

import socket
import json
import os
import sys

# MicroPython có gc, CPython cũng có nhưng ít cần
try:
    import gc
except ImportError:
    gc = None


class WebServer:
    """Non-blocking HTTP server phục vụ Dashboard và API."""

    def __init__(self, port=80):
        self.port = port
        self.sock = None
        # Callbacks — sẽ được gán từ main.py
        self.on_get_data = None      # callback() → dict
        self.on_set_mode = None      # callback(mode: int)
        self.on_set_pump = None      # callback(pump: int, state: int)
        self.on_sync_time = None     # callback(data: dict)

    def start(self):
        """Khởi tạo và bind server socket."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", self.port))
        self.sock.listen(5)
        self.sock.settimeout(0.1)  # Non-blocking: timeout 100ms
        print("[webserver] Listening on 0.0.0.0:{}".format(self.port))

    def poll(self):
        """Kiểm tra và xử lý 1 request (nếu có). Non-blocking."""
        try:
            client, addr = self.sock.accept()
        except OSError:
            # Không có kết nối mới (timeout) → bỏ qua
            return
        except Exception:
            return

        try:
            client.settimeout(2.0)
            request = self._recv_request(client)
            if request:
                self._handle_request(client, request)
        except Exception as e:
            print("[webserver] Error: " + str(e))
        finally:
            try:
                client.close()
            except Exception:
                pass
            if gc:
                gc.collect()

    def _recv_request(self, client):
        """Nhận toàn bộ HTTP request từ client."""
        try:
            data = client.recv(2048)
            if data:
                return data.decode("utf-8")
        except Exception:
            pass
        return None

    def _handle_request(self, client, request):
        """Routing: phân tích request và gọi handler phù hợp."""
        # Lấy dòng đầu tiên: "GET /path HTTP/1.1"
        first_line = request.split("\r\n")[0]
        parts = first_line.split(" ")
        if len(parts) < 2:
            return

        method = parts[0]
        path = parts[1]

        print("[webserver] {} {}".format(method, path))

        # ----- Routing -----
        if method == "OPTIONS":
            # CORS Preflight — cho phép browser gửi cross-origin requests
            self._handle_cors_preflight(client)
        elif method == "GET" and path == "/":
            self._serve_html(client)
        elif method == "GET" and path == "/favicon.ico":
            # Trả về 204 No Content thay vì 404 để tránh log lỗi liên tục
            self._send_response(client, 204, "text/plain", "")
        elif method == "GET" and path == "/api/data":
            self._handle_api_data(client)
        elif method == "POST" and path == "/api/mode":
            body = self._extract_body(request)
            self._handle_api_mode(client, body)
        elif method == "POST" and path == "/api/pump":
            body = self._extract_body(request)
            self._handle_api_pump(client, body)
        elif method == "POST" and path == "/api/time":
            body = self._extract_body(request)
            self._handle_api_time(client, body)
        else:
            self._send_response(client, 404, "text/plain", "Not Found")

    # ---- Route Handlers ----

    def _serve_html(self, client):
        """Phục vụ file www/index.html (truyền từng chunk tiết kiệm RAM)."""
        # Tìm file index.html
        html_path = self._find_html_path()
        if not html_path:
            self._send_response(client, 404, "text/plain", "index.html not found")
            return

        try:
            file_size = os.stat(html_path)[6]
        except Exception:
            file_size = 0

        # Gửi header
        header = "HTTP/1.1 200 OK\r\n"
        header += "Content-Type: text/html; charset=utf-8\r\n"
        if file_size > 0:
            header += "Content-Length: {}\r\n".format(file_size)
        header += "Connection: close\r\n\r\n"
        client.send(header.encode("utf-8"))

        # Gửi body theo từng chunk 512 bytes
        # CPython cần encoding="utf-8" để đọc emoji/unicode
        # MicroPython không hỗ trợ param encoding nhưng mặc định đọc UTF-8
        from config import MOCK_MODE
        if MOCK_MODE:
            f = open(html_path, "r", encoding="utf-8")
        else:
            f = open(html_path, "r")
        try:
            while True:
                chunk = f.read(512)
                if not chunk:
                    break
                client.send(chunk.encode("utf-8"))
        finally:
            f.close()

    def _handle_api_data(self, client):
        """GET /api/data → trả về JSON dữ liệu cảm biến + trạng thái."""
        data = {}
        if self.on_get_data:
            data = self.on_get_data()
        self._send_json(client, data)

    def _handle_api_mode(self, client, body):
        """POST /api/mode → đặt chế độ hoạt động."""
        try:
            obj = json.loads(body)
            mode = int(obj.get("mode", 0))
            if self.on_set_mode:
                self.on_set_mode(mode)
            self._send_json(client, {"ok": True, "mode": mode})
        except Exception as e:
            self._send_json(client, {"ok": False, "error": str(e)}, status=400)

    def _handle_api_pump(self, client, body):
        """POST /api/pump → điều khiển bơm thủ công (chỉ MODE 0)."""
        try:
            obj = json.loads(body)
            pump = int(obj.get("pump", 1))
            state = int(obj.get("state", 0))
            if self.on_set_pump:
                result = self.on_set_pump(pump, state)
                if result is False:
                    self._send_json(client, {
                        "ok": False,
                        "error": "Chỉ điều khiển được ở chế độ Thủ công (MODE 0)"
                    }, status=403)
                    return
            self._send_json(client, {"ok": True, "pump": pump, "state": state})
        except Exception as e:
            self._send_json(client, {"ok": False, "error": str(e)}, status=400)

    def _handle_api_time(self, client, body):
        """POST /api/time -> đồng bộ RTC hệ thống."""
        try:
            obj = json.loads(body)
            if self.on_sync_time:
                self.on_sync_time(obj)
            self._send_json(client, {"ok": True})
        except Exception as e:
            self._send_json(client, {"ok": False, "error": str(e)}, status=400)

    # ---- Utilities ----

    def _find_html_path(self):
        """Tìm đường dẫn tới index.html (tương thích cả MicroPython và CPython)."""
        # Trên CPython: dùng đường dẫn tương đối với file script
        # Trên MicroPython: dùng đường dẫn tuyệt đối
        candidates = ["www/index.html", "/www/index.html"]
        try:
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            candidates.insert(0, os.path.join(script_dir, "www", "index.html"))
        except Exception:
            pass  # MicroPython có thể không hỗ trợ sys.argv
        for p in candidates:
            try:
                os.stat(p)
                return p
            except OSError:
                continue
        return None

    def _extract_body(self, request):
        """Tách body từ HTTP request (sau \\r\\n\\r\\n)."""
        parts = request.split("\r\n\r\n", 1)
        if len(parts) > 1:
            return parts[1]
        return ""

    def _handle_cors_preflight(self, client):
        """Xử lý CORS preflight request (OPTIONS)."""
        header = "HTTP/1.1 204 No Content\r\n"
        header += "Access-Control-Allow-Origin: *\r\n"
        header += "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        header += "Access-Control-Allow-Headers: Content-Type\r\n"
        header += "Access-Control-Max-Age: 86400\r\n"
        header += "Connection: close\r\n\r\n"
        client.send(header.encode("utf-8"))

    def _send_response(self, client, status, content_type, body):
        """Gửi HTTP response."""
        status_text = {200: "OK", 204: "No Content", 400: "Bad Request", 403: "Forbidden", 404: "Not Found"}
        header = "HTTP/1.1 {} {}\r\n".format(status, status_text.get(status, ""))
        if status == 204:
            # 204 No Content — không gửi body
            header += "Connection: close\r\n\r\n"
            client.send(header.encode("utf-8"))
            return
        header += "Content-Type: {}; charset=utf-8\r\n".format(content_type)
        header += "Content-Length: {}\r\n".format(len(body.encode("utf-8")))
        header += "Connection: close\r\n\r\n"
        client.send(header.encode("utf-8"))
        client.send(body.encode("utf-8"))

    def _send_json(self, client, data, status=200):
        """Gửi JSON response với CORS header."""
        body = json.dumps(data)
        status_text = {200: "OK", 400: "Bad Request", 403: "Forbidden"}
        header = "HTTP/1.1 {} {}\r\n".format(status, status_text.get(status, ""))
        header += "Content-Type: application/json\r\n"
        header += "Access-Control-Allow-Origin: *\r\n"
        header += "Content-Length: {}\r\n".format(len(body.encode("utf-8")))
        header += "Connection: close\r\n\r\n"
        client.send(header.encode("utf-8"))
        client.send(body.encode("utf-8"))

    def stop(self):
        """Dừng server."""
        if self.sock:
            self.sock.close()
            print("[webserver] Stopped")
