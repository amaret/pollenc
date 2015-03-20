POLLENC
===========

##The Amaret Cloud Compiler Client

The pollenc package is part of the pypi index:

https://pypi.python.org/pypi/pollenc

#INSTALL

`sudo pip install pollen`

#UN-INSTALL

`sudo pip uninstall pollen`

#DEVELOPER NOTES

To run the pollen command from source, use the pip command:

## RUNNING FROM SRC
* clone the pollenc repo
* cd into the pollenc dir
* `pip install -e .`

The output of the pip command tells you the path of the symlink that will
run your code - as you edit it and change it.  No need to run the pip command
again unless you move your repo.

Example: `Installing pollen script to /Users/navicore/Library/Python/2.7/bin`

So the above user just adds that dir to PATH if it wasn't already included.

## LOG LEVELS

log levels are controlled by the environment variable `LOG_LEVEL`.

To debug, use:

`LOGLEVEL=DEBUG pollen ...`

To trace, use:

`LOGLEVEL=TRACE pollen ...`

