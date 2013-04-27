#!/usr/bin/env python

# Copyright 2012, 2013 Amaret Inc. All rights reserved.

import sys
import datetime
import bernhard
import os
sys.path.append(sys.path[0] + os.sep + '..' + os.sep + 'wind.lib')

sys.path.insert(1, "/etc/amaret")
import config

import SocketServer
import StringIO
import threading
import redis
import syslog
import json
import traceback
import WindData

rmmonitor = bernhard.Client(host=config.riemann['host'])

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
        return redis.Redis(host=config.redis['host'], port=config.redis['port'])

    #
    # begin redis usage
    #
    def getQName(self, compiler):
        if compiler == 'pollen_avr_gcc':
            return 'CLC_POLLEN_AVR_GCC_1_0'
        if compiler == 'pollen_msp430_gcc':
            return 'CLC_POLLEN_MSP430_GCC_1_0'
        if compiler == 'msp430_gcc':
            return 'CLC_MSP430_GCC_1_0'
        if compiler == 'avr_gcc':
            return 'CLC_AVR_GCC_1_0'
        if compiler == 'arduino':
            return 'CLC_ARDUINO_1_0'
        if compiler == 'pollen_any':   #for translateonly
            return 'CLC_POLLEN_AVR_GCC_1_0'

        raise Exception('PollenServer: unsupported compiler: %s' % (compiler))

    def write(self, qname, dstr):
      self.getRdis().lpush(qname, dstr);
    
    def read(self, replyQueue):
        response = self.getRdis().brpop(keys=[replyQueue], timeout=30);
        if ( not response or not len(response) == 2) :
            raise Exception('bad response from clc: %s' % (response))
        return response[1]

    def handleError(self, etxt):
        syslog.syslog(syslog.LOG_ERR, etxt)
        ERROR_MSG_OBJ['content']['error'] = etxt
        emsgtxt = json.dumps(ERROR_MSG_OBJ)
        hmsg = "%i\n%s" % (len(emsgtxt), emsgtxt)
        self.request.send(hmsg)
    #
    # end redis usage
    #

    def validateToken(self, token):
        t = WindData.findOne('clc.tokens', {'token': token, 'active': True})
        if t != None:
            del t['_id']
            syslog.syslog(syslog.LOG_ERR, json.dumps(t))
        return t != None
        #return token == 'rustyisacowboy'
    
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
                        
            try:
                dataobj = json.loads(data)
            except ValueError, e:
                self.handleError(str(e))
                return

            token = dataobj["user"]["token"]
            if not self.validateToken(token):
                etxt = 'invalid token \'%s\'' % (token)
                self.handleError(etxt)
                return

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
                #tobj = dataobj
                #tbytes = tobj['content']['content']
                #base64.b64decode(tbytes)

                break
        except Exception, e:
            self.handleError(str(e))
        except:
            e = sys.exc_info()[0]
            self.logexception(1)
            etxt = 'pollenc exception %s (%s)' % (e.__class__, e)
            self.handleError(etxt)
        
        stoptime = datetime.datetime.now()
        dur = stoptime - starttime
        mdur = dur.microseconds
        if mdur > 0:
            mdur = mdur / 1000 # we only care about milliseconds
        state = 'ok'
        if mdur > 1000000:
            state = 'warning'
       
        rmmonitor.send({'host': config.riemann['clienthost'], 'service': 'pollenc-txn-dur', 'metric': mdur, 'description': 'pollenc txn duration in milliseconds', 'state': state})

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

    syslog.syslog(syslog.LOG_INFO, 'service starting using redis host %s:%s' % (config.redis['host'], config.redis['port']))
    
    address = (config.pollenc['interface'], config.pollenc['port'])
    server = PollencServer(address, PollencRequestHandler)

    server.serve_forever()

    syslog.syslog(syslog.LOG_INFO, 'service stopping')

    server.socket.close()

