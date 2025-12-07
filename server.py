# -*- coding: utf-8 -*-
from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import logging
import os
from urllib.parse import urlparse
from datetime import datetime

CERT_FILE = r"cert.pem"
KEY_FILE = r"key.pem"
PORT = 443
LOG_FILE = r"server.log"

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.path = "/close.html"
        logging.info(f"{self.client_address[0]} requested {self.path}")
        try:
            super().do_GET()
        except Exception as e:
            logging.error(f"Error serving {self.path}: {e}")

    def log_message(self, format, *args):
        logging.info("%s - %s" % (self.address_string(), format % args))

# Ensure working directory is correct
os.chdir(os.path.dirname(os.path.abspath(__file__)))

server_address = ("0.0.0.0", PORT)
httpd = HTTPServer(server_address, MyHandler)

# Setup SSL
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

logging.info(f"HTTPS server starting on port {PORT}")

try:
    httpd.serve_forever()
except Exception as e:
    logging.error(f"Server stopped with error: {e}")
finally:
    httpd.server_close()
    logging.info("Server stopped.")
