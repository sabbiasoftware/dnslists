#!/usr/bin/env bash
sudo systemctl stop pihole-FTL.service
sudo sqlite3 /etc/pihole/pihole-FTL.db ".backup /home/rpi/pihole/pihole-FTL.bak.db"
sudo sqlite3 /etc/pihole/pihole-FTL.db "DELETE FROM query_storage WHERE timestamp <= strftime('%s', datetime('now', '-30 day'));"
sudo sqlite3 /etc/pihole/pihole-FTL.db "VACUUM;"
sudo systemctl start pihole-FTL.service
