import subprocess
from pathlib import Path

HOSTS_FILE = r"C:\Windows\System32\drivers\etc\hosts"
CERT_FILE = "cert.pem"
KEY_FILE = "key.pem"
SERVER_FILE = "server.py"
HTTPS_PORT = 4443

# 1. Read all domains for 127.0.0.1
def get_local_domains(hosts_path):
    domains = []
    with open(hosts_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("127.0.0.1"):
                parts = line.split()
                domains.extend(parts[1:])
    return domains

domains = get_local_domains(HOSTS_FILE)
if not domains:
    raise RuntimeError("No domains found for 127.0.0.1 in hosts file!")

# 2. Prepare OpenSSL config with SAN
openssl_conf = Path("openssl_san.cnf")
san_entries = "\n".join([f"DNS.{i+1} = {d}" for i, d in enumerate(domains)])
cn_domain = domains[0]  # First domain as CN

conf_text = f"""
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = {cn_domain}

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
{san_entries}
"""
openssl_conf.write_text(conf_text, encoding="utf-8")

# 3. Remove old cert/key
for f in [CERT_FILE, KEY_FILE]:
    p = Path(f)
    if p.exists():
        p.unlink()

from pathlib import Path

CERT_FILE = "cert.pem"
KEY_FILE = "key.pem"

# Remove old cert and key if they exist
for f in [CERT_FILE, KEY_FILE]:
    p = Path(f)
    if p.exists():
        print(f"Removing old file: {f}")
        p.unlink()


# 4. Generate new self-signed certificate
print("Generating new self-signed certificate for domains:", domains)
subprocess.run([
    "openssl", "req", "-x509", "-nodes", "-days", "365",
    "-newkey", "rsa:2048",
    "-keyout", KEY_FILE,
    "-out", CERT_FILE,
    "-config", str(openssl_conf)
], check=True)

# 5. Update server.py
server_code = f"""\
# -*- coding: utf-8 -*-
from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl

CERT_FILE = r"{CERT_FILE}"
KEY_FILE = r"{KEY_FILE}"
HTTPS_PORT = {HTTPS_PORT}

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

print(f"HTTPS server running on port {{HTTPS_PORT}}. Open in browser e.g. https://{cn_domain}:{{HTTPS_PORT}}/close.html")
httpd.serve_forever()
"""

Path(SERVER_FILE).write_text(server_code, encoding="utf-8")
print(f"{SERVER_FILE} updated and ready to run.")
