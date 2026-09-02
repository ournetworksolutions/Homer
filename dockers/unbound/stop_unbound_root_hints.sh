#!/bin/bash
echo "[$(date +"%d-%m-%Y %H:%M")] Unbound DNS Root Hints Updater Service has ended" >> "log.txt"
killall unbound_root_hints.sh


