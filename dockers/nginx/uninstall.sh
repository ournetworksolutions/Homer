#!/bin/bash
sudo systemctl stop update-certs.timer
sudo systemctl disable --now update-certs.timer
sudo systemctl daemon-reload
sudo rm -rf /etc/systemd/system/update-certs.service
sudo rm -rf /etc/systemd/system/update-certs.timer
echo ""
echo "Done"
