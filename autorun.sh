#!/bin/bash

# go to folder where script is (i.e. root of source)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR

while [[ True ]]; do
    #statements
    python3 main.py
    if [[ $? -eq 0 ]]; then
        echo "application exited cleanly, not restarting"
        break
    else
        read -n 1 -r -s -p "Press any key to restart application, or [Q] to exit." key
        if [ "$key" == "q" ] || [ "$key" == "Q" ]; then
            break
        fi
    fi
done
