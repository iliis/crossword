#!/bin/bash

# otherwise it somehow doesn't correctly start
sleep 1

while [[ True ]]; do
    python3 main.py
    if [[ $? -eq 0 ]]; then
        echo "application exited cleanly, restarting immediately"
    else
        read -n 1 -r -s -p "Press any key to restart application" key
    fi
done
