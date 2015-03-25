# Copyright Amaret, Inc 2011-2015. All rights reserved.
''' Pollen Cloud Compiler Socket Protocol Impl '''
# pylint: disable=bad-whitespace

import socket
import json
from pollen.scrlogger import ScrLogger

BUFSZ = 1024


class Socker(object):
    ''' Pollen Cloud Compiler Socket Protocol Impl '''

    def __init__(self, host, port):

        self.log = ScrLogger()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.log.debug("connecting to %s:%s" % (host,
                                                port))
        self.sock.connect((host, port))

    def write(self, obj):
        ''' write obj as json'''
        msg = json.dumps(obj)
        hmsg = "%i\n%s" % (len(msg), msg)
        self.sock.send(hmsg)

    def read(self):
        ''' read obj as json'''
        hlen = 0
        hlen_rec = ''
        while True:
            byt = self.sock.recv(1)
            if byt == '\n':
                hlen = int(hlen_rec)
                break
            hlen_rec += byt

        rec = ''
        while len(rec) < hlen:
            siz = BUFSZ
            rem = hlen - len(rec)
            if rem < BUFSZ:
                siz = rem
            byt = self.sock.recv(siz)
            rec += byt
        return json.loads(rec)

    def talk(self, request_obj):
        ''' read and write'''

        self.write(request_obj)

        while True:

            workobj = self.read()
            self.log.trace(workobj)

            if workobj['type'] == 'userlog':
                self.log.ulog(workobj)
                continue
            if workobj['type'] != 'response':
                continue
            if workobj['content']['error'] != 'None':
                print 'pollenc error! %s' % (workobj['content']['error'])
                return
            break

        return workobj

