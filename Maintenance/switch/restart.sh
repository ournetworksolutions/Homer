#!/bin/bash
sudo -u "main" bash -c '
cd /home/main/Documents/Maintenance/
source venv/bin/activate
python switch_reboot.py'