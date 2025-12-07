# -*- coding: utf-8 -*-
import os
import subprocess

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

# Generate SAN config for OpenSSL
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

# Remove old certificate (same CN)
try:
    subject = domains[0]
    subprocess.run([
        "certutil", "-delstore", "root", subject
    ], check=False)
    print(f"Old certificate for {subject} removed if it existed.")
except Exception as e:
    print("Could not remove old certificate:", e)

# Import certificate into Trusted Root store
try:
    subprocess.run([
        "certutil", "-addstore", "-f", "root", CERT_FILE
    ], check=True)
    print("Certificate imported into Trusted Root Certification Authorities.")
except Exception as e:
    print("Could not import certificate automatically:", e)


# Rewrite server.py (logging-enabled version)
server_code = f"""# -*- coding: utf-8 -*-
from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import logging
import os
from urllib.parse import urlparse
from datetime import datetime

CERT_FILE = r"{CERT_FILE}"
KEY_FILE = r"{KEY_FILE}"
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
        logging.info(f"{{self.client_address[0]}} requested {{self.path}}")
        try:
            super().do_GET()
        except Exception as e:
            logging.error(f"Error serving {{self.path}}: {{e}}")

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

logging.info(f"HTTPS server starting on port {{PORT}}")

try:
    httpd.serve_forever()
except Exception as e:
    logging.error(f"Server stopped with error: {{e}}")
finally:
    httpd.server_close()
    logging.info("Server stopped.")
"""

with open(SERVER_FILE, "w", encoding="utf-8") as f:
    f.write(server_code)

print(f"Updated {SERVER_FILE} and generated new certificate for domains: {', '.join(domains)}")
# Optionally, start the server