# Copyright Amaret, Inc 2011-2015. All rights reserved.
''' Pollen Cloud Compiler Client Lib'''

import sys
import os

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
PINK = '\033[95m'
CYAN = '\033[96m'
BLUE = '\033[34m'
WHITE = '\33[97m'


def has_colours(stream):
    ''' has color'''
    if not hasattr(stream, "isatty"):
        return False
    if not stream.isatty():
        return False  # auto color only on TTYs
    try:
        # pylint: disable=bare-except
        import curses
        curses.setupterm()
        return curses.tigetnum("colors") > 2
    except:
        # guess false in case of error
        return False

LEVELS = [
    "ERROR",
    "WARN",
    "NOTICE",
    "INFO",
    "DEBUG",
    "TRACE"
]


class ScrLogger(object):
    ''' obj '''

    def __init__(self):

        self.has_colours = has_colours(sys.stdout)

        self.level = os.getenv('LOGLEVEL', 'INFO')

        self.indentsize = 2

        self.levels = {
            'NOTICE': {'color': CYAN},
            'INFO':   {'color': GREEN},
            'WARN':   {'color': YELLOW},
            'ERROR':  {'color': RED},
            'DEBUG':  {'color': BLUE},
            'TRACE':  {'color': GREEN},
        }

        level_idx = LEVELS.index(self.level)
        for lvl in self.levels.keys():
            idx = LEVELS.index(lvl)
            if idx > level_idx:
                del self.levels[lvl]

    def printout(self, text, colour=None):
        ''' print '''
        if self.has_colours and colour is not None:
            # seq = "\x1b[1;%dm" % (30+colour) + text + "\x1b[0m"
            # seq = "\x1b[1;%s" % ("\033[95m") + text + "\x1b[0m"
            seq = "\x1b[1;%s" % (colour) + text + "\x1b[0m"
            sys.stdout.write(seq)
        else:
            sys.stdout.write(text)

    def output(self, level, message, indent, newline):
        ''' out '''
        if level in self.levels.keys():
            try:
                indent = " " * (self.indentsize * indent)
            except TypeError:
                indent = ""

            if level == "DEBUG" or level == "TRACE" or level == "ERROR":
                self.printout("[" + level.lower() + "] ",
                              self.levels[level]['color'])

            sys.stdout.write(indent + str(message))
            if newline is True:
                sys.stdout.write("\n")

    def notice(self, message, indent=0, newline=True):
        ''' f '''
        self.output("NOTICE", '', indent, newline)
        self.output("NOTICE", message, indent, newline)

    def info(self, message, indent=0, newline=True):
        ''' f '''
        self.output("INFO", message, indent, newline)

    def warn(self, message, indent=0, newline=True):
        ''' f '''
        self.output("WARN", message, indent, newline)

    def error(self, message, indent=0, newline=True):
        ''' f '''
        self.output("ERROR", message, indent, newline)

    def debug(self, message, indent=0, newline=True):
        ''' f '''
        self.output("DEBUG", message, indent, newline)

    def ulog(self, msgobj, indent=0, trace=False):
        ''' f '''
        level = msgobj['content']['level']
        msg = msgobj['content']['source']

        if trace is False and level != "TRACE":
            if level == "OUTPUT":
                self.notice(msg, indent)
            else:
                self.output(level, msg, indent, True)
        # else:
            # print trace info for the ulog message...

    def trace(self, message, indent=0, newline=True):
        ''' f '''
        if self.level < LEVELS.index("TRACE"):
            return

        if 'type' in message:
            if message['type'] == 'userlog':
                self.ulog(message, indent, trace=True)
            elif message['type'] == 'request':
                self.trace_request(message, indent)
            elif message['type'] == 'response':
                self.trace_response(message, indent)
            return

        else:
            self.output("TRACE", message, indent, newline)

    def trace_request(self, message, indent=0):
        ''' f '''
        self.output("TRACE", "compile request, tid: %s, aid: %s" %
                    (str(message['tid']), str(message['aid'])), indent, True)

        self.output("TRACE", "compiler: %s, mcu: %s, cflags: %s, props: %s" %
                    (message['compiler'], message['content']['mcu'],
                     message['cflags'], message['props']), indent, True)

        self.output("TRACE", "entry: %s, environment: %s, print module: %s" %
                    (message['content']['entry'], message['env'],
                     message['prn']), indent, True)

        self.output("TRACE", "bundles: %s" % str(message['bundles']), indent,
                    True)

    def trace_response(self, message, indent=0):
        ''' f '''
        self.output("TRACE", "compile response, tid: %s, aid: %s" %
                    (str(message['tid']), str(message['aid'])), indent, True)

        self.output("TRACE", "user id: %s, file built: %s, "
                    "error %s" % (message['user']['id'],
                                  message['content']['entry'],
                                  message['content']['error']), indent, True)
