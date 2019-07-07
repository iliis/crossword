#!/bin/bash

#xrandr --output DVI-I-1 --mode 1024x768

# go to folder where script is (i.e. root of source)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR

# disable CTRL key
xmodmap -e 'keycode 37 = NoSymbol'
xmodmap -e 'keycode 135 = NoSymbol'

# ALT
xmodmap -e 'keycode 64 = NoSymbol'
xmodmap -e 'keycode 108 = NoSymbol'

# make sure numlock is OFF (otherwise the right-hand side of the EEE's keyboard becomes numbers)
numlockx off

# hide mouse cursor
unclutter -idle 2.00 -root &

# actually launch crossword
xfce4-terminal --fullscreen --hide-menubar --hide-scrollbar --hide-toolbar --command "bash autorun_mainloop.sh"
