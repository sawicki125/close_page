# -*- coding: utf-8 -*-
from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl

CERT_FILE = r"cert.pem"
KEY_FILE = r"key.pem"
HTTPS_PORT = 4443

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "/close.html"
        return super().do_GET()

server_address = ("0.0.0.0", HTTPS_PORT)
httpd = HTTPServer(server_address, MyHandler)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

print(f"HTTPS server running on port {HTTPS_PORT}. Open in browser e.g. https://allideasofanime.com:{HTTPS_PORT}/close.html")
httpd.serve_forever()
