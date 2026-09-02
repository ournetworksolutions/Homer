#!/bin/bash
echo "Install sshpass package!"
echo "qBitorrent tested compatible version (5.1.4 - 5.2.3)"
cp Desktop/*.desktop /home/$USER/Desktop/
sudo mkdir -p /opt/Homer
sudo cp -r homer.py /opt/Homer/homer.py
sleep 1
sudo sed -i 's/\r$//' /opt/Homer/homer.py
sleep 1
sudo cp -r apple-touch-icon.png /opt/Homer/apple-touch-icon.png
sudo cp -r favicon.ico /opt/Homer/favicon.ico
sudo cp -r icon-192.png /opt/Homer/icon-192.png
sudo cp -r icon-512.png /opt/Homer/icon-512.png
sudo chmod +x /opt/Homer/homer.py
sudo cp homer.service /etc/systemd/system/homer.service
sudo systemctl daemon-reload
sudo systemctl enable --now homer.service
sudo systemctl start homer.service &
systemctl status homer.service
echo ""
echo "Done"
