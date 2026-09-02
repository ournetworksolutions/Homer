#!/bin/bash

# 1. Systemd Requirements
# Explicitly set the CAROOT path so mkcert works in the background
export CAROOT="/root/.local/share/mkcert"

# 1. Configuration
# Match this to your exact container name in docker-compose
CONTAINER_NAME="nginx-proxy-manager" 

# Match this to the folder you found in Step 1
# Ensure you are running this script from the same directory as your docker-compose.yml
DEST_DIR="./data/custom_ssl/npm-1"
DEST_DIR_TAILSCALE="./data/custom_ssl/npm-2"

# Tailnet DNS name
DNS_NAME="main.tailscale.ts.net"

# Make sure this matches your actual Tailscale container name
TAILSCALE_CONTAINER="tailscale" 



# Ensure destination folders exist so chmod doesn't fail
mkdir -p "$DEST_DIR"
mkdir -p "$DEST_DIR_TAILSCALE"

# 2. Generate ONE certificate covering all domains directly into NPM's folder
# We name them fullchain.pem and privkey.pem because that is what NPM looks for
echo "==> Generating Tailscale Certificate..."
docker exec -it "$TAILSCALE_CONTAINER" tailscale cert $DNS_NAME
docker exec "$TAILSCALE_CONTAINER" cat "$DNS_NAME.crt" > "$DEST_DIR_TAILSCALE/fullchain.pem"
docker exec "$TAILSCALE_CONTAINER" cat "$DNS_NAME.key" > "$DEST_DIR_TAILSCALE/privkey.pem"

echo "==> Generating Unified SAN Certificate..."
mkcert -cert-file "$DEST_DIR/fullchain.pem" \
       -key-file "$DEST_DIR/privkey.pem" \
       "*.homer.com" "homer.com" \
       "*.homer.com" "homer.com"

echo "==> Setting correct file permissions..."
chmod 644 "$DEST_DIR/fullchain.pem" "$DEST_DIR/privkey.pem"
chmod 644 "$DEST_DIR_TAILSCALE/fullchain.pem" "$DEST_DIR_TAILSCALE/privkey.pem"

echo "==> Hot-reloading Nginx Proxy Manager..."
# 3. Reload Nginx inside the container seamlessly to apply the new cert
docker exec "$CONTAINER_NAME" nginx -s reload

echo "----------------------------------------"
echo "Done! Certificates generated and NPM reloaded."
echo "Install and trust this Root CA directory on your devices:"
mkcert -CAROOT
echo "/root/.local/share/mkcert/rootCA.pem"
