#!/usr/bin/env python

# Copyright 2012, 2013 Amaret Inc. All rights reserved.

import SocketServer
import StringIO
import threading
import redis
import argparse
import syslog
import json
import sys
import traceback
import base64

rdis = ''
ERROR_MSG = '{\"tid\": \"0\", \"aid\": \"0\", \"type\": \"response\", \"service\": \"compile\", \"user\": {\"id\": \"0\", \"name\": \"None\"}, \"project\": {\"id\": \"0\", \"name\": \"None\"}, \"content\" : {\"content\": \"None\", \"filename\": \"None\", \"error\": \"%s\" }}'

class PollencRequestHandler(SocketServer.BaseRequestHandler):

    #
    # begin redis usage
    #
    def getQName(self, e):
        if e == 'msp430':
            return 'CLC_MSP430_1_0'
        if e == 'arduino':
            return 'CLC_ARDUINO_1_0'
        if e == 'pollen':
            return 'CLC_POLLEN_1_0'
        raise Exception('unsupported envoronment: %s' % (e))

    def write(self, qname, dstr):
	    rdis.lpush(qname, dstr);
    
    def read(self, replyQueue):
        response = rdis.brpop(keys=[replyQueue], timeout=30);
        if ( not response or not len(response) == 2) :
            raise Exception('bad response from clc: %s' % (response))
        return response[1]
    #
    # end redis usage
    #

    def validateToken(self, token):
        #todo:
        return token == 'rustyisacowboy'
    
    def handle(self):
        try:
            hlen = 0
            hlenRec = ''
            while True:
                b = self.request.recv(1)
                if b == '\n':
                    hlen = int(hlenRec)
                    break
                hlenRec += b

            BUFSZ = 1024
            data = ''
            while len(data) < hlen:
                sz = BUFSZ
                rem = hlen - len(data)
                if rem < BUFSZ:
                    sz = rem
                b = self.request.recv(sz)
                data += b

            dataobj = ''
            try:
                dataobj = json.loads(data)
            except ValueError, e:
                self.request.send('%s' % (str(e)))
                syslog.syslog(syslog.LOG_WARNING, 'pollenc rejecting bad msg: %s' % (e))
                return

            token = dataobj["user"]["token"]
            if not self.validateToken(token):
                syslog.syslog(syslog.LOG_WARNING, 'pollenc rejecting token %s' % (token))
                emsg =  ERROR_MSG % ('bad token')
                hmsg = "%i\n%s" % (len(emsg), emsg)
                self.request.send(hmsg)
                return

            syslog.syslog(syslog.LOG_INFO, 'pollenc request handler invoked for token %s' % (token))
            cur_thread = threading.currentThread()
            responseQueue = 'POLLENC_REPLYTO_QUEUE_%s_%s' % (cur_thread.getName(), dataobj["user"]["name"])
            dataobj["reply"] = responseQueue
            qname = self.getQName(dataobj['environment']);
            self.write(qname, json.dumps(dataobj))

            while True:
                response = self.read(responseQueue)
                hmsg = "%i\n%s" % (len(response), response)
                self.request.send(hmsg)
                dataobj = json.loads(response)
                if dataobj['type'] != 'response':
                    continue
                try:
                    tobj = dataobj
                    tbytes = tobj['content']['content']
                    syslog.syslog(syslog.LOG_INFO, 'ejs testing sent data of len %i' % (len(tbytes)))
                    base64.b64decode(tbytes)
                except Exception, e:
                    syslog.syslog(syslog.LOG_INFO, 'ejs error: %s' % (str(e)))

                break
            return
        except:
            e = sys.exc_info()[0]
            self.logexception(1)
            syslog.syslog(syslog.LOG_ERR, 'pollenc exception %s (%s)' % (e.__class__, e))

    def logexception(self, includetraceback = 0):
        exctype, exception, exctraceback = sys.exc_info()
        excclass = str(exception.__class__)
        message = str(exception)

        if not includetraceback:
            syslog.syslog(syslog.LOG_ERR, "%s: %s" % (excclass, message))
        else:
            excfd = StringIO.StringIO()
            traceback.print_exception(exctype, exception, exctraceback, None,
                                      excfd)
            for line in excfd.getvalue().split("\n"):
                syslog.syslog(syslog.LOG_ERR, line)


class PollencServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--rdishost', dest='rdishost', action='store', help='redis server hostname')
    parser.add_argument('--rdisport',  dest='rdisport', action='store', help='redis server port', type=int)
        
    args = parser.parse_args()

    if args.rdishost == None:
        args.rdishost = "localhost"

    if args.rdisport == None:
        args.rdisport = 6379

    syslog.syslog(syslog.LOG_INFO, 'service starting using redis host %s:%s' % (args.rdishost, args.rdisport))
    rdis = redis.Redis(host=args.rdishost, port=args.rdisport)
    
    address = ('0.0.0.0', 2323)
    server = PollencServer(address, PollencRequestHandler)

    server.serve_forever()

    syslog.syslog(syslog.LOG_INFO, 'service stopping')

    server.socket.close()

