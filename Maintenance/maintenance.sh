#!/bin/bash

# Our scipts working path
WORKING_PATH="/home/main/Documents/Maintenance"

cd $WORKING_PATH
source venv/bin/activate
python ui.py "$WORKING_PATH/log.txt" &
notify-send -i printer-network "Maintenance" "Service has started"
echo "[$(date +"%d-%m-%Y %H:%M")] Maintenance Service has started" >> "$WORKING_PATH/log.txt"

while true; do
    # 2. Check Internet Connectivity
    # -c 4 : Send exactly 4 ping requests
    # -W 2 : Wait 2 seconds for a response
    # > /dev/null 2>&1 : Hide the standard ping output from the terminal
    if ping -c 4 -W 2 8.8.8.8 > /dev/null 2>&1; then
        # Check 1: Ping was successful
        sleep 60
    else
        # Check 1 FAILED
        echo "[$(date +"%d-%m-%Y %H:%M")] Warning (1/3): Internet seems down. Waiting 60s..." >> "$WORKING_PATH/log.txt"
        sleep 60
        
        # --- THE DOUBLE CHECK ---
        if ping -c 4 -W 2 8.8.8.8 > /dev/null 2>&1; then
            echo "[$(date +"%d-%m-%Y %H:%M")] Internet restored on check 2. False alarm." >> "$WORKING_PATH/log.txt"
        else
            # Check 2 FAILED
            echo "[$(date +"%d-%m-%Y %H:%M")] Warning (2/3): Internet is still down. Waiting 60s for another check..." >> "$WORKING_PATH/log.txt"
            sleep 60
            
            # --- THE TRIPLE CHECK ---
            if ping -c 4 -W 2 8.8.8.8 > /dev/null 2>&1; then
                echo "[$(date +"%d-%m-%Y %H:%M")] Internet restored on check 3. False alarm." >> "$WORKING_PATH/log.txt"
            else
                # Check 3 FAILED
                echo "[$(date +"%d-%m-%Y %H:%M")] Warning (3/3): Internet is still down. Waiting 60s for final check..." >> "$WORKING_PATH/log.txt"
                sleep 60

                # --- THE LAST CHECK ---
                if ping -c 4 -W 2 8.8.8.8 > /dev/null 2>&1; then
                    echo "[$(date +"%d-%m-%Y %H:%M")] Internet restored on last check. False alarm." >> "$WORKING_PATH/log.txt"
                else
                    # Last Check 4 FAILED. Confirmed dead.
                    echo "[$(date +"%d-%m-%Y %H:%M")] Error (4/4): Internet confirmed unreachable. Rebooting network stack..." >> "$WORKING_PATH/log.txt"
                    python router_reboot.py
                    sleep 5
                    python switch_reboot.py

                    # Sleep for 5 minutes to give the router time to fully boot up and connect
                    sleep 300
                fi
            fi
        fi
    fi
done