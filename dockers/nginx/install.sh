#!/bin/bash
sudo cp update-certs.service /etc/systemd/system/update-certs.service
sudo cp update-certs.timer /etc/systemd/system/update-certs.timer
sudo systemctl daemon-reload
sudo systemctl enable --now update-certs.timer
sudo systemctl status update-certs.timer
echo ""
echo "Done"
