#!/bin/bash

#xrandr --output DVI-I-1 --mode 1024x768

# go to folder where script is (i.e. root of source)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR

# disable CTRL key
xmodmap -e 'keycode 135 = NoSymbol'

# hide mouse cursor
unclutter -idle 2.00 -root &

# otherwise it somehow doesn't correctly start
sleep 1

# actually launch crossword
xfce4-terminal --fullscreen --hide-menubar --hide-scrollbar --hide-toolbar --command "bash autorun_mainloop.sh"
