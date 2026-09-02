#!/bin/bash

mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -config cert.cnf
openssl x509 -in certs/cert.pem -outform der -out certs/vaultwarden.cer
echo ""
echo ""
echo "Your token: $(openssl rand -base64 48)"
