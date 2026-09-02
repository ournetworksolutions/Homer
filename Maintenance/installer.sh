#!/bin/bash
echo "[Desktop Entry]
Encoding=UTF-8
Version=0.9.4
Type=Application
Name=Maintenance
Icon=printer-network
Exec=$PWD/maintenance.sh
OnlyShowIn=XFCE;
RunHook=0
StartupNotify=false
Terminal=false
Hidden=false" > /home/$USER/.config/autostart/Maintenance.desktop
python -m venv venv
source venv/bin/activate
pip install selenium
pip install webdriver-manager
echo "Done"
