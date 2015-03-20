# pylint: disable=missing-docstring
''' Pollen Cloud Compiler Client Lib'''

import sys

class ScrLogger(object):

    def __init__(self, level="INFO"):

        self.indentsize = 2
        self.colors = {'END': '\033[0m', 'LightRed': '\033[91m', 'LightGreen':
                       '\033[92m', 'LightYellow': '\033[93m', 'LightBlue':
                       '\033[94m', 'LightPink': '\033[95m', 'LightCyan':
                       '\033[96m', 'Blue': '\033[34m', 'White': '\33[97m'}

        self.level_array = ["NOTICE", "INFO", "WARN", "ERROR", "DEBUG",
                            "TRACE"]

        self.level = "INFO"
        if level in self.level_array:
            self.level = self.level_array.index(level)

        self.levels = {
            'NOTICE': {'color': self.colors['LightCyan']},
            'INFO':   {'color': self.colors['LightYellow']},
            'WARN':   {'color': self.colors['LightPink']},
            'ERROR':  {'color': self.colors['White']},
            'DEBUG':  {'color': self.colors['LightGreen']},
            'TRACE':  {'color': self.colors['LightGreen']},
        }

    def output(self, level, message, indent, newline):
        if level in self.levels.keys():
            indent = " " * (self.indentsize * indent)
            sys.stdout.write(self.levels[level]['color'])

            if level == "DEBUG" or level == "TRACE" or level == "ERROR":
                sys.stdout.write("[" + level.lower() + "] ")

            sys.stdout.write(indent + message)
            sys.stdout.write(self.colors["END"])
            if newline is True:
                sys.stdout.write("\n")

    def notice(self, message, indent=0, newline=True):
        self.output("NOTICE", message, indent, newline)

    def info(self, message, indent=0, newline=True):
        self.output("INFO", message, indent, newline)

    def warn(self, message, indent=0, newline=True):
        self.output("WARN", message, indent, newline)

    def error(self, message, indent=0, newline=True):
        self.output("ERROR", message, indent, newline)

    def debug(self, message, indent=0, newline=True):
        self.output("DEBUG", message, indent, newline)

    def ulog(self, msgobj, indent=0, trace=False):
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
        if self.level < self.level_array.index("TRACE"):
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
        self.output("TRACE", "compile response, tid: %s, aid: %s" %
                    (str(message['tid']), str(message['aid'])), indent, True)

        self.output("TRACE", "user id: %s, user name: %s, file built: %s, "
                    "error %s" % (message['user']['id'],
                                  message['user']['name'],
                                  message['content']['entry'],
                                  message['content']['error']), indent, True)

