#!/usr/bin/env bash
# Generates self-signed TLS certificates for local HTTPS reverse proxy testing
set -euo pipefail

CERT_DIR="./docker/certs"
mkdir -p "$CERT_DIR"

if [ -f "$CERT_DIR/server.crt" ] && [ -f "$CERT_DIR/server.key" ]; then
    echo "TLS certificates already exist in $CERT_DIR. Skipping generation."
    exit 0
fi

echo "Generating self-signed SSL/TLS certificates..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$CERT_DIR/server.key" \
    -out "$CERT_DIR/server.crt" \
    -subj "/C=IN/ST=Karnataka/L=Bengaluru/O=AlgionsAILabs/OU=DevOps/CN=localhost"

chmod 600 "$CERT_DIR/server.key"
chmod 644 "$CERT_DIR/server.crt"
echo "Certificates generated successfully in $CERT_DIR"
