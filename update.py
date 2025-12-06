# -*- coding: utf-8 -*-
import os
import subprocess
import ssl
from datetime import datetime

# Paths
SERVER_FILE = "server.py"
CERT_FILE = "cert.pem"
KEY_FILE = "key.pem"
OPENSSL_CONFIG = "openssl_san.cnf"

# Read hosts file and extract domains pointing to 127.0.0.1
hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
domains = []
with open(hosts_path, "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and line.startswith("127.0.0.1"):
            parts = line.split()
            if len(parts) > 1:
                domains.extend(parts[1:])

if not domains:
    print("No local domains found in hosts file.")
    exit(1)

# Generate SAN config
san_config = f"""
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = {domains[0]}

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = {', '.join(f'DNS:{d}' for d in domains)}
"""

with open(OPENSSL_CONFIG, "w") as f:
    f.write(san_config)

# Remove old certs
for f in [CERT_FILE, KEY_FILE]:
    if os.path.exists(f):
        os.remove(f)

# Generate new cert/key
subprocess.run([
    "openssl", "req", "-x509", "-nodes", "-days", "365",
    "-newkey", "rsa:2048",
    "-keyout", KEY_FILE,
    "-out", CERT_FILE,
    "-config", OPENSSL_CONFIG
], check=True)

# Rewrite server.py
server_code = f"""# -*- coding: utf-8 -*-
from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import os

CERT_FILE = r"{CERT_FILE}"
KEY_FILE = r"{KEY_FILE}"
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

print(f"HTTPS server running on port {{HTTPS_PORT}}")
httpd.serve_forever()
"""

with open(SERVER_FILE, "w", encoding="utf-8") as f:
    f.write(server_code)

print(f"Updated {SERVER_FILE} and generated new certificate for domains: {', '.join(domains)}")
