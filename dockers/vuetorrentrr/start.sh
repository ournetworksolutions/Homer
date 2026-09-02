#!/bin/bash
sshpass -p 'YOUR_REMOTE_SSH_SERVER_PASSWORD' ssh -o StrictHostKeyChecking=no gamebox@10.10.10.9 'cd /home/gamebox_user/Documents/qbittorrent && ./start.sh'

