#!/bin/bash
docker compose down
docker compose pull
sleep 3
docker compose up -d
