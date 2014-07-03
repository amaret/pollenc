#!/usr/bin/env python

# Copyright 2012, 2013 Amaret Inc. All rights reserved.

import sys
import datetime
import os

#sys.path.append(sys.path[0] + os.sep + '..' + os.sep + 'wind.lib')
#sys.path.insert(1, "/etc/amaret")
#import config
#import WindData

import config
import SocketServer
import StringIO
import threading
import redis
import syslog
import json
import traceback
#from riemann import RiemannClient, RiemannUDPTransport

#rmmonitor = RiemannClient(transport = RiemannUDPTransport, host=config.riemann['host'])

REDIS_HOST = ""
REDIS_PORT = 0
TCP_HOST= ''
TCP_PORT= 0

MAX_MSG_SIZE = 1000000

ERROR_MSG_OBJ = {
                'tid': 0, 
                'aid': 0, 
                'type': 'response', 
                'service': 'compile', 
                'user': {
                    'id': 0, 
                    'name': 
                    'None'
                    }, 
                'project': {
                    'id': 0, 
                    'name': 
                    'None'
                    }, 
                'content' : {
                    'content': 'None', 
                    'filename': 'None'
                    }
                }


class PollencRequestHandler(SocketServer.BaseRequestHandler):

    def getRdis(self):
        return redis.Redis(REDIS_HOST, REDIS_PORT)

    #
    # begin redis usage
    #
    def getQName(self, compiler): 
        qName = config.redisQueues[compiler] 
        if not qName:
            raise Exception('problem in toolchain specification')
        return qName

    def write(self, qname, dstr):
      self.getRdis().lpush(qname, dstr);
    
    def read(self, replyQueue):
        response = self.getRdis().brpop(keys=[replyQueue], timeout=30);
        if ( not response or not len(response) == 2) :
            raise Exception('bad response from clc: %s' % (response))
        return response[1]

    def handleError(self, etxt):
        syslog.syslog(syslog.LOG_ERR, etxt)
        traceback.print_exc(file=sys.stdout)
        self.sendErrorStats()     
        ERROR_MSG_OBJ['content']['error'] = etxt
        emsgtxt = json.dumps(ERROR_MSG_OBJ)
        hmsg = "%i\n%s" % (len(emsgtxt), emsgtxt)
        self.request.send(hmsg)
    #
    # end redis usage
    #

    def handle(self):
        starttime = datetime.datetime.now()
        try:
            syslog.syslog(syslog.LOG_DEBUG, 'handler invoked')
            hlen = 0
            hlenRec = ''
            while True:
                b = self.request.recv(1)
                if b == '':
                    syslog.syslog(syslog.LOG_WARNING, 'recv returned unexpectedly, rejecting.')
                    return
                if b == '\n':
                    hlen = int(hlenRec)
                    break
                hlenRec += b
                if len(hlenRec) > 10:
                    syslog.syslog(syslog.LOG_WARNING, 'rejecting bad header: %s' % (hlenRec))
                    self.request.send('invalid header: %s\n' % (hlenRec))
                    return
            
            syslog.syslog(syslog.LOG_DEBUG, 'processing')
            syslog.syslog(syslog.LOG_DEBUG, 'msg header len: %i' % (hlen))
            
            if hlen > MAX_MSG_SIZE or hlen == 0:
                syslog.syslog(syslog.LOG_WARNING, 'rejecting bad msg size header: %s' % (hlen))
                self.request.send('invalid msg size: %i\n' % (hlen))
                return

            BUFSZ = 1024
            data = ''
            while len(data) < hlen:
                sz = BUFSZ
                rem = hlen - len(data)
                if rem < BUFSZ:
                    sz = rem
                b = self.request.recv(sz)
                syslog.syslog(syslog.LOG_DEBUG, 'read %i bytes' % (len(b)))
                data += b

            dataobj = ''
            syslog.syslog(syslog.LOG_DEBUG, 'total bytes read: %i' % (len(data)))
                        
            try:
                dataobj = json.loads(data)
            except ValueError, e:
                self.handleError(str(e))
                return

            token = dataobj["user"]["token"]

            syslog.syslog(syslog.LOG_INFO, 'pollenc request handler invoked for token %s' % (token))
            cur_thread = threading.currentThread()
            responseQueue = 'POLLENC_REPLYTO_QUEUE_%s_%s' % (cur_thread.getName(), dataobj["user"]["token"])
            dataobj["reply"] = responseQueue
            qname = self.getQName(dataobj['compiler']);
            self.write(qname, json.dumps(dataobj))

            while True:
                response = self.read(responseQueue)
                hmsg = "%i\n%s" % (len(response), response)
                self.request.send(hmsg)
                dataobj = json.loads(response)
                if dataobj['type'] != 'response':
                    continue

                break
            self.sendStats(starttime)     
        except Exception, e:
            self.handleError(str(e))
        except:
            e = sys.exc_info()[0]
            self.logexception(1)
            etxt = 'pollenc exception %s (%s)' % (e.__class__, e)
            self.handleError(etxt)

        return

    def sendErrorStats(self):
        state = 'warning'

        #rmmonitor.send({'host': config.riemann['clienthost'], 'service': 'pollenc exception', 'metric': 1, 'description': 'pollenc txn failed', 'state': state})
        return

    def sendStats(self, starttime):
        stoptime = datetime.datetime.now()
        dur = stoptime - starttime
        mdur = dur.microseconds
        if mdur > 0:
            mdur = mdur / 1000 # we only care about milliseconds
        else:
            raise Exception('PollenServer: impossible duration %s' % (mdur))
        state = 'ok'
        if mdur > 1000:
            state = 'warning'
        elif mdur > 10000:
            state = 'critical'
       
        #rmmonitor.send({'host': config.riemann['clienthost'], 'service': 'pollenc txn-dur', 'metric': mdur, 'description': 'pollenc txn duration in milliseconds', 'state': state})
        return

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


    REDIS_HOST = config.redis['host']
    REDIS_PORT = config.redis['port']
    TCP_HOST = config.pollenc_tcp['interface'] 
    TCP_PORT = config.pollenc_tcp['port']

    syslog.syslog(syslog.LOG_INFO, 'service starting using redis host %s:%s' % ((REDIS_HOST, REDIS_PORT))) 
    
    address = ((TCP_HOST, TCP_PORT)) 
    server = PollencServer(address, PollencRequestHandler)

    server.serve_forever()

    syslog.syslog(syslog.LOG_INFO, 'service stopping')

    server.socket.close()

