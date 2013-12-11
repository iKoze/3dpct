3dpct
=====

3d printer control toolchain for reprap machines

Main purpose?
-------------

Command line tool for 3d printing with a reprap machine from given G-code.


What's this?
------------

3dpct is a simple lightweight python script which lets you control your 3d printer using G-code.

Features:
* __G-code parser__:
  It provides a simple G-code parser which removes G-code comments and empty lines, so that only the necessary information
  will be sent to the reprap machine.
* __Checksum generator__:
  The parser also adds a line number and checksum to each line of G-code, so that the
  3d printer is able to indicate transmission errors and re-requests corrupt lines of G-code.
* __Code sender__:
  3dpct overtakes the whole printer communication for you. You just have to feed it with the G-code file and the printer
  device (baudrate).
* __G-code cli__:
  3dpct also provides a cli which turns you able to write gcode on the command line and send it directly to the printer

All features are packed into two python classes, which you could also use in your own python program.


But how?
--------

Example usage:
* __Print a model__:

  ```
  ./3dpct.py -f model.gcode -p -d /dev/ttyUSB0 -b 250000
  ```

* __Output filtered G-code__:

  ```
  ./3dpct.py -f model.gcode -o
  ```

* __Use as part of a pipeline__:

  ```
  cat model.gcode | ./3dpct.py -f - -o > filtered_gcode.gcode
  ```

* __Simple command execution (without checksum and line numbers)__:

  ```
  ./3dpct.py --no-checksum -e G28
  ```

Please also check out the -h option:

```
usage: 3dpct.py [-h] [-f [FILE]] [-o] [-p] [-c] [-n] [-e ...] [--no-checksum]
                [--silent] [-d [DEVICE]] [-b [BAUD]]

3dpct - a 3d printer control toolchain

optional arguments:
  -h, --help            show this help message and exit
  -f [FILE], --file [FILE]
                        load gcode from given file name or use '-' for STDIN
  -o, --output          output filtered gcode to STDOUT
  -p, --print           use 3d printer to print gcode
  -c, --cli             start a cli for manual printer control using gcodes
  -n, --no-direction-mark
                        don't show direction marks and prompt (eg: <~: ,~>:
                        ,<-: )
  -e ..., --execute ...
                        execute a single gcode line (must be last argument)
  --no-checksum         don't generate line numbers and checksums
  --silent              don't output communication while printing
  -d [DEVICE], --device [DEVICE]
                        the device to use for printing (default: /dev/ttyUSB0)
  -b [BAUD], --baud [BAUD]
                        the baudrate to use on device (default: 250000)
```

Disclaimer
----------

The programm has only been tested with a Velleman K8200. Please contact me if you get errors with your reprap (Just open a GitHub issue). Then I'll try to fix them. Please also let me know if it works with your reprap.

See also
--------

* http://reprap.org
* http://reprap.org/wiki/G-code

