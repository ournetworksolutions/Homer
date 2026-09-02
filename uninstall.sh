#!/bin/bash
sudo systemctl stop homer.service
sudo systemctl disable --now homer.service
sudo systemctl daemon-reload
sudo rm -f /etc/systemd/system/homer.service
sudo rm -rf /opt/Homer
echo "Done"



