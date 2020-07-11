Crossword Puzzle Thingy
=======================

This is a small application for an adventure room.
It presents the user with a crossword puzzle to solve.

Changes are transmitted in real-time over a basic TCP connection to the room manager.


Installation
============

Fedora:

    sudo dnf install python3-pyserial python3-netifaces unclutter numlockx xfce4-terminal openbox

Recommendation: use lightdm as display manager

To launch it:

    python3 main.py

If you can't get a connection to the crossword application, but the network is otherwise fine, open the correct port:

    sudo firewall-cmd --permanent --add-port=1234/tcp

The autorun.sh script disables ALT and CTRL keys. However, other shortcuts
(e.g. F1 or F10 for xfce4-terminal) still work. For xfce4-terminal, edit
~/.config/xfce4/terminal/accels.scm

To disable F1 key UNcomment fullscreen line and add EMPTY accelerator handler:

    (gtk_accel_path "<Actions>/terminal-window/fullscreen" "")

To disable F10 keys use the mouse in the graphical xfce4 settings and disable F10 etc.


## Screen Size

The application currently needs a terminal with at least 39 rows and 102 columns (mainly due to the size of the shooting range gui).

Use `resize -s $rows $cols` to change the terminal size.


Autostart
================

Install openbox. Graphically select log in with the "Openbox" session type. This should autostart openbox from now on. 

Add this line to ~/.config/openbox/autostart:

    ~/crossword/autorun.sh
    

Remote Interface
================

The application supports remote control and status debug over TCP.
Packets are JSON-data, prefixed with the payload length:

    $LEN\n$DATA\n

(Last newline is optional)

For example, the following command stops the application:

    {
        'command': 'quit'
    }

This is encoded as:

    19\n{"command": "quit"}\n

In python you can write this as:

    cmd = {'command': 'quit'}
    data = json.dumps(cmd)
    pkt = "{}\n{}\n".format(len(data), data).encode('ascii')

See also `test_send_command.py` for some examples.


Responses
---------

The application replies to every incoming packet with a response packet or by closing the connection in case of a malformed packet.

The response always has the following format:

    {
        'command': 'response,
        'retval':  $RETVAL,
        'reply_to': $ORIG_PACKET
    }

`$RETVAL` can be one of the following

- *`success`*: The command was executed successfully
- *`failure`*: Could not execute the command (e.g. because an invalid parameter was given)
- *`exception`*: Something went wrong that really should not have

In the case of a failure or exception, there an additional field 'error' is provided, detailing what went wrong.
In the case of an exception, there are also the fields 'exception', 'exception_type' and 'traceback' which give even more details.

`$ORIG_PACKET` is simply a verbatim copy of the command that was received. This
could be used to uniquely identify a response, e.g. by including an 'id' field
in the original command


Commands
--------

- *ping*: Dummy command to check if application is still alive


    {'command': 'ping'}

- *quit*: Exit application
- *reset*: Reset application
- *shutdown*: Shuts down PC. Needs sudo without password for `halt` command.
- *show_popup*: Show a popup message to user. The parameter 'buttons' is optional and defaults to 'OK'

```
    {
        'command': 'show_popup',
        'title':   'Hinweis',
        'text':    'Sie haben noch 5 Minuten Zeit übrig!',
        'buttons': ['OK','BLA','BLUBB']
    }
```

- *get_time*: Returns the current time left for the game in seconds.
- *set_time*: Updates the game timer.

```
    {
        'command': 'set_time',
        'timeout': 120,
    }
```

- *show_shooting_range*: Shows shooting range window ;)
- *restore_saved_state*: Load backup from disk (if any). Useful if application crashed.
- *wakeup*: Send a key to wake up application from sleep / exit screensaver.


Events
------

The Application can also send out packets on its own whenever something
potentially interesting happens. No response to these packets is expected.

For example, whenever the crossword is edited, the following event is sent:

    {
        "event": "puzzle_state_update",
        "kind": "edited",
        "state": {
            "cursor": {
                "x": 0,
                "y": 6
            },
            "input": ["ASDFSA", "BL", "AFSA", "FSAFDSAFSA", "     ", "ACE", "FSAFA", "S         ", "        "],
            "solved_fraction": 0.2222222222222222,
            "solutionstate": [
                ["WRONG", [false, false, false, false, false, false]],
                ["CORRECT", [true, true]],
                ["WRONG", [false, false, false, false]],
                ["WRONG", [false, false, true, false, false, false, false, false, false, false]],
                ["UNSOLVED", [false, false, false, false, false]],
                ["CORRECT", [true, true, true]],
                ["WRONG", [false, false, false, false, false]],
                ["UNSOLVED", [false, false, false, false, false, false, false, false, false, false]],
                ["UNSOLVED", [false, false, false, false, false, false, false, false]]
            ]
        }
    }

The cursor position is absolute and does NOT take horizontal offset of word into account!

`solutionstate` says how close to a solution every word is (can be either
`UNSOLVED`, `PARTIALLY_CORRECT`, `CORRECT` or `WRONG`) and also for every
character if it is correct or not.


Whenever a window opens or closes a `window_stack_update` event is sent:

    {
        "event": "window_stack_update",
        "top_window": {
            "type": "popup",
            "title": "blabla",
            "text": "Lorem Ipsum Dolore Solet"
        }
    }
