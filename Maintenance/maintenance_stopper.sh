#!/bin/bash
echo "[$(date +"%d-%m-%Y %H:%M")] Maintenance Service has ended" >> "log.txt"
killall maintenance.sh
pkill -f "python ui.py"
notify-send -i printer-network "Maintenance" "Service has ended"

