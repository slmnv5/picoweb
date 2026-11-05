import socket

import machine
import network


led = machine.Pin("LED", machine.Pin.OUT)
led.off()

ONE_K: int = 1024
SSID = "picoweb"
PASS = "88888888"
HTTP_PORT: int = 80

MAIN_PAGE: str = """
<html>
<head>
    <meta charset='utf-8'>
</head>
<body>
<h1><p>Server address: {serv_addr}</p></h1>
<h2><p>Client address: {cli_addr}</p></h2>
<h2><p>Client request: {request}</p></h2>
<h3><p>Past data:</p><h3>
<p>{visits}</p>

</body>
</html>
"""


class MyServer:

    def __init__(self) -> None:
        self._alive: bool = True
        print(f"Use ssid {SSID} password: {PASS}")
        self._acc_pnt = network.WLAN(network.AP_IF)
        self._acc_pnt.config(essid=SSID, password=PASS)
        self._acc_pnt.active(True)
        while not self._acc_pnt.active():
            pass

        self._addr_dic: dict[str, int] = dict()
        print('Connection successful', self._acc_pnt.ifconfig())

    def _add_to_dic(self, addr: str):
        if addr in self._addr_dic:
            self._addr_dic[addr] += 1
        else:
            self._addr_dic[addr] = 1

    def serve(self):
        led.on()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", HTTP_PORT))
        sock.listen(5)
        conn: socket.socket = None
        addr: tuple
        serv_addr = f"{self._acc_pnt.ifconfig()[0]}:{HTTP_PORT}"
        print("Serving web pages", self._acc_pnt.ifconfig())
        while self._alive:
            try:
                conn, addr = sock.accept()
                led.on()
                self._add_to_dic(f"{addr[0]}:{HTTP_PORT}")
                request: str = conn.recv(ONE_K).decode().split("\r\n")[0]
                if request.startswith("GET /"):
                    conn.send(b'HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                    s = MAIN_PAGE.format(cli_addr=addr[0], visits=str(self._addr_dic), serv_addr=serv_addr, request=request)
                    conn.send(s.encode())
                else:
                    conn.send(b"HTTP/1.0 303 See other\r\nContent-Type: text/html\r\nLocation: /\r\n\r\n")
            except Exception as ex:
                print(f'Error in serve loop: {ex}')
                self._add_to_dic(str(ex))
                self._alive = False
            finally:
                conn.close()
                led.off()


MyServer().serve()
