# -*- coding: utf-8 -*-
import os
import subprocess

# --- CONFIG ---
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
LIST_FILE = "host_list.txt"
SERVER_FILE = "server.py"
CERT_FILE = "cert.pem"
KEY_FILE = "key.pem"
OPENSSL_CONFIG = "openssl_san.cnf"


# --- STEP 1: Load host_list.txt and add missing entries ---
if not os.path.exists(LIST_FILE):
    print("host_list.txt not found.")
    exit(1)

with open(HOSTS_PATH, "r", encoding="utf-8") as f:
    existing_lines = f.read().splitlines()

existing_hosts = set(line.strip().lower() for line in existing_lines)

with open(LIST_FILE, "r", encoding="utf-8") as f:
    domains_to_add = [line.strip().lower() for line in f if line.strip()]

new_entries = []
for domain in domains_to_add:
    base = f"127.0.0.1 {domain}"
    www = f"127.0.0.1 www.{domain}"

    if base not in existing_hosts:
        new_entries.append(base)

    if www not in existing_hosts:
        new_entries.append(www)

if new_entries:
    with open(HOSTS_PATH, "a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(new_entries) + "\n")

    print("Added entries:")
    for e in new_entries:
        print("  " + e)
else:
    print("No new host entries needed.")


# --- STEP 2: Re-scan hosts file to get all domains for certificate generation ---
domains = []
with open(HOSTS_PATH, "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and line.startswith("127.0.0.1"):
            parts = line.split()
            if len(parts) > 1:
                domains.extend(parts[1:])

if not domains:
    print("No local domains found in hosts file.")
    exit(1)


# --- STEP 3: Create an OpenSSL SAN config ---
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
subjectAltName = {', '.join('DNS:' + d for d in domains)}
"""

with open(OPENSSL_CONFIG, "w") as f:
    f.write(san_config)


# --- STEP 4: Remove old cert files if they exist ---
for f in [CERT_FILE, KEY_FILE]:
    if os.path.exists(f):
        os.remove(f)


# --- STEP 5: Generate certificate ---
subprocess.run([
    "openssl", "req", "-x509", "-nodes", "-days", "365",
    "-newkey", "rsa:2048",
    "-keyout", KEY_FILE,
    "-out", CERT_FILE,
    "-config", OPENSSL_CONFIG
], check=True)


# --- STEP 6: Delete old certificate from store ---
subject = domains[0]
subprocess.run([
    "certutil", "-delstore", "root", subject
], check=False)

print(f"Old certificate for {subject} deleted (if existed).")


# --- STEP 7: Import new certificate ---
try:
    subprocess.run([
        "certutil", "-addstore", "-f", "root", CERT_FILE
    ], check=True)
    print("New certificate imported into Trusted Root.")
except Exception as e:
    print("Could not import certificate automatically:", e)


print(f"Generated new certificate for domains:\n  {', '.join(domains)}")
