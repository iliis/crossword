#!/bin/bash

while [[ True ]]; do
    #statements
    python3 main.py
    if [[ $? -eq 0 ]]; then
        echo "application exited cleanly, not restarting"
        break
    fi
done
