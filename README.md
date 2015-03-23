POLLENC
===========

##The Amaret Cloud Compiler Client

The pollenc package is part of the pypi index:

https://pypi.python.org/pypi/pollenc

#INSTALL

`sudo pip install pollen`

begin exploring the pollen command with:

`pollen --help`

#UN-INSTALL

`sudo pip uninstall pollen`

#DEVELOPER NOTES

To develop, test, and debug the pollen client you must clone the git
repository and register your src copy with pip.  Your src copy will then
be in your python2 path but as a symbolic link so that your edits to your
src copy have immediate effect.

## RUNNING FROM SRC VIA PIP
* clone the pollenc repo
* cd into the pollenc dir
* `pip install -e .`

The output of the pip command tells you the path of the symlink that will
run your code - as you edit it and change it.  No need to run the pip command
again unless you move your repo.

Example: `Installing pollen script to /Users/navicore/Library/Python/2.7/bin`

So the above user just adds that dir to PATH if it wasn't already included.

## PRINT STACK TRACES

The main.py entrypoint catches all exceptions and prints them according to
the log levels (see below).  Use the TRACE log level to see the call stack
if you are getting errors.

## LOG LEVELS

log levels are controlled by the environment variable `LOG_LEVEL`.

To debug, use:

`LOGLEVEL=DEBUG pollen ...`

To trace, use:

`LOGLEVEL=TRACE pollen ...`

