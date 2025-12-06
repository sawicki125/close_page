# -*- coding: utf-8 -*-
from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import os

CERT_FILE = r"cert.pem"
KEY_FILE = r"key.pem"
HTTPS_PORT = 443

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.path = "/close.html"
        return super().do_GET()

    def list_directory(self, path):
        # Serve close.html instead of directory listing
        close_path = os.path.join(os.getcwd(), "close.html")
        if os.path.exists(close_path):
            with open(close_path, "rb") as f:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.send_header("Content-length", str(os.path.getsize(close_path)))
                self.end_headers()
                self.wfile.write(f.read())
            return None
        else:
            return super().list_directory(path)

server_address = ("0.0.0.0", HTTPS_PORT)
httpd = HTTPServer(server_address, MyHandler)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

print(f"HTTPS server running on port {HTTPS_PORT}")
httpd.serve_forever()
