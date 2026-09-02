#!/bin/bash

# Our scipts working path
WORKING_PATH="/home/main/Documents/Homer/dockers/unbound"

cd $WORKING_PATH
echo "[$(date +"%d-%m-%Y %H:%M")] Unbound DNS Root Hints Updater Service has started" >> "$WORKING_PATH/log.txt"
while true; do
    dow=$(date +%w)        # 0 = Sunday
    hour=$(date +%H)
    minute=$(date +%M)

    # convert time to minutes since midnight
    time=$((10#$hour * 60 + 10#$minute))

    start=270 # 04:30 = 4*60 + 30
    end=290   # 04:50 = 4*60 + 50

    if [ "$dow" -eq 0 ] && [ "$time" -ge "$start" ] && [ "$time" -le "$end" ]; then
        curl -o root.hints https://www.internic.net/domain/named.root
        mv root.hints unbound/root.hints
        ./restart.sh
        sleep 2400 # sleep 40 minutes to prevent spamming multiple times in the same window
        echo "[$(date +"%d-%m-%Y %H:%M")] Root hints updated; Unbound DNS restarted to apply changes" >> "$WORKING_PATH/log.txt"
    else
        sleep 60   # check again soon
    fi
done
