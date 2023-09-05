#!/bin/bash
date > uptime.log
#backup old log, with date
cp latest.log backups/$(date +%Y-%m-%d_%H.%M.%S).log
#back up the database
cp userdb.json backups/$(date +%Y-%m-%d_%H.%M.%S).json
source ./env/bin/activate
#run the script, and save the log and errors
python bot.py | tee latest.log 2>&1 
