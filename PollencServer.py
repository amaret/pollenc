#!/usr/bin/env python

# Copyright 2012, 2013 Amaret Inc. All rights reserved.

#import WindData    (mongo database, or something. For tokens)
import sys
import datetime
import dateutil.parser
import os
import config
import SocketServer
import StringIO
import threading
import redis
import syslog
import json
import traceback
import socket
sys.path.insert(1, "/home/ops/repos/amaret.pylib/riemann")
import RiemannMonitor
sys.path.insert(1, "/home/ops/repos/amaret.pylib/email")
import Email

rmmonitor = None

REDIS_HOST = ""
REDIS_PORT = 0
REDIS_MAXWAIT = 600
TCP_HOST= ''
TCP_PORT= 0

ERROR_MSG_OBJ = {
                'tid': 0, 
                'aid': 0, 
                'type': 'response', 
                'service': 'compile', 
                'user': {
                    'id': 0, 
                    'name': 'None'
                    }, 
                'project': {
                    'id': 0, 
                    'name': 'None'
                    }, 
                'content' : {
                    'content': 'None', 
                    'filename': 'None'
                    }
                }
LOG_MSG_OBJ = {
                'tid': 0, 
                'aid': 0, 
                'type': 'userlog', 
                'service': 'compile', 
                'user': {
                    'id': 0, 
                    'name': 'None'
                    }, 
                'project': {
                    'id': 0, 
                    'name': 'None'
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
      syslog.syslog(syslog.LOG_DEBUG, 'redis push: queue %s' % (qname) )
      self.getRdis().lpush(qname, dstr);

    def readwait(self, wait, replyQueue):
        if (wait <= 0):
            self.sendEmail('urgent', "Server blocked on redis pop. Server returned 'bad response' to user.")
            self.handleError('bad response from clc: blocked on redis pop')
            raise Exception('bad response from clc: blocked on redis pop')
        self.sendUserLog('NOTICE', 'server delay: waiting on compile job queue...')
        response = self.getRdis().brpop(keys=[replyQueue], timeout=60);
        if (not response) :
            syslog.syslog(syslog.LOG_INFO, 'redis queue wait (60 sec)')
            response = self.readwait(wait - 60, replyQueue)
        if (not len(response) == 2) :
            self.sendEmail('urgent', "Server gets bad response from worker. Server returned 'bad response' to user.")
            raise Exception('bad response from clc: %s' % (response))
        return response

    
    def read(self, replyQueue):
        syslog.syslog(syslog.LOG_DEBUG, 'redis pop: queue key %s' % (replyQueue) )
        starttime = datetime.datetime.now()
        response = self.getRdis().brpop(keys=[replyQueue], timeout=30);
        if (not response) :
            syslog.syslog(syslog.LOG_INFO, 'redis queue wait (30 sec)')
            self.sendEmail('serious', "Server slow: waiting on redis pop.")
            response = self.readwait(REDIS_MAXWAIT, replyQueue)
        if (not len(response) == 2) :
            self.sendEmail('urgent', "Server gets bad response from worker. Server returned 'bad response' to user.")
            raise Exception('bad response from clc: %s' % (response))
        rmmonitor.send_timing_event({'tags': ["pollenc_server_job"]}, \
            starttime, \
            'pollenc_server redis_brpop_wait', \
            'pollenc_server redis brpop wait duration in milliseconds')
        return response[1]

    def handleError(self, etxt):
        syslog.syslog(syslog.LOG_ERR, etxt)
        traceback.print_exc(file=sys.stdout)
        self.sendErrorStats()     
        ERROR_MSG_OBJ['content']['error'] = etxt
        emsgtxt = json.dumps(ERROR_MSG_OBJ)
        hmsg = "%i\n%s" % (len(emsgtxt), emsgtxt)
        self.request.send(hmsg)


    def sendUserLog(self, level, msg):
        content = {'level': level, 'source': msg}
        LOG_MSG_OBJ['content'] = content
        emsgtxt = json.dumps(LOG_MSG_OBJ)
        hmsg = "%i\n%s" % (len(emsgtxt), emsgtxt)
        self.request.send(hmsg)

    def sendEmail(self, severe, msg):
        txt = Email.getEmail('clc_msg.txt')
        txt = txt.replace('[[ hostname ]]', socket.gethostname())
        txt = txt.replace('[[ severity ]]', severe)
        txt = txt.replace('[[ message ]]', msg)
        Email.send("ops@amaret.com", "ops@amaret.com", "Cloud Compiler Message", txt)


    def validateToken(self, token):
        #WindData is the mongo database (I think)
        #t = WindData.findOne('clc.tokens', {'token': token, 'active': True})
        #if t != None:
        #    del t['_id']
        #    syslog.syslog(syslog.LOG_ERR, json.dumps(t))
        #return t != None
        return True

    #
    # end redis usage
    #

    def handle(self):
        starttime = datetime.datetime.now()
        # get the compile request
        try:
            syslog.syslog(syslog.LOG_DEBUG, 'handler invoked')
            hlen = 0
            hlenRec = ''
            while True:
                b = self.request.recv(1)
                if b == '':
                    self.sendEmail('warning', "recv returned unexpectedly, rejecting compile job.")
                    syslog.syslog(syslog.LOG_WARNING, 'recv returned unexpectedly, rejecting.')
                    return
                if b == '\n':
                    hlen = int(hlenRec)
                    break
                hlenRec += b
                if len(hlenRec) > 10:
                    self.sendEmail('warning', "recv returned unexpectedly, rejecting compile job.")
                    syslog.syslog(syslog.LOG_WARNING, 'rejecting bad header: %s' % (hlenRec))
                    self.request.send('invalid header: %s\n' % (hlenRec))
                    return
            
            syslog.syslog(syslog.LOG_DEBUG, 'processing')
            syslog.syslog(syslog.LOG_DEBUG, 'msg header len: %i' % (hlen))

            MAX = config.clcConstants["MAX_MSG_SIZE"]

            if hlen > MAX or hlen == 0:
                syslog.syslog(syslog.LOG_WARNING, 'rejecting bad msg size header: %s' % (hlen))
                #handleError() does not transmit error to client
                self.handleError(("Uploaded zip file has size %i, exceeds Pollen cloud compiler maximum size of %i") %(hlen, MAX))
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
            rmmonitor.send_timing_event({'tags': ["pollenc_server_job"]}, \
                starttime, \
                'pollenc_server recv_from_client_dur', \
                'pollenc_server recv from client duration in milliseconds')
                        
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

            xferstarttime = dateutil.parser.parse(dataobj['xferstarttime'])
            rmmonitor.send_timing_event({'tags': ["network_transfer"]}, \
                xferstarttime, \
                'pollenc_client xfer_to_svr', \
                'pollenc_client send to server duration in milliseconds')

            syslog.syslog(syslog.LOG_INFO, 'pollenc worker invoked for token %s' % (token))
            cur_thread = threading.currentThread()
            responseQueue = 'POLLENC_REPLYTO_QUEUE_%s_%s' % (cur_thread.getName(), dataobj["user"]["token"])
            dataobj["reply"] = responseQueue
            qname = self.getQName(dataobj['compiler']);

            # send the compile request to worker
            sendstarttime = datetime.datetime.now()
            dataobj['xferstarttime'] = sendstarttime.isoformat()
            self.write(qname, json.dumps(dataobj))
            rmmonitor.send_timing_event({'tags': ["pollenc_server_job"]}, \
                sendstarttime, \
                'pollenc_server send_to_wkr_dur', \
                'pollenc_server send to worker duration in milliseconds')

            recvstarttime = datetime.datetime.now()
            sendstarttime = datetime.datetime.now()

            LOG_MSG_OBJ['tid'] =  dataobj['tid']
            LOG_MSG_OBJ['aid'] =  dataobj['aid']
            LOG_MSG_OBJ['user'] = dataobj['user']

            while True:
                # get the worker response from response queue
                response = self.read(responseQueue)
                dataobj = json.loads(response)
                if dataobj['type'] == 'response':
                    xferstarttime = dateutil.parser.parse(dataobj['xferstarttime'])
                    rmmonitor.send_timing_event({'tags': ["network_transfer"]}, \
                        xferstarttime, \
                        'redisque_wait_wkr_to_svr', \
                        'redisque_wait xfer from wkr to svr duration in milliseconds')
                    rmmonitor.send_timing_event({'tags': ["pollenc_server_job"]}, \
                        recvstarttime, \
                        'pollenc_server recv_from_wkr_dur', \
                        'pollenc_server recv from worker includes compile duration in milliseconds')
                    sendstarttime = datetime.datetime.now()
                hmsg = "%i\n%s" % (len(response), response)

                # send worker response to client
                self.request.send(hmsg)
                if dataobj['type'] != 'response':
                    continue       # a log message

                break     

            rmmonitor.send_timing_event({'tags': ["pollenc_server_job"]}, \
                sendstarttime, \
                'pollenc_server send_to_client_dur', \
                'pollenc_server send to client duration in milliseconds')

            rmmonitor.send_timing_event({'tags': ["pollenc_server_job"]}, \
                starttime, \
	        'pollenc_server total txn_dur', \
                'pollenc_server total txn duration in milliseconds') 

        except Exception, e:
            self.handleError(str(e))
        except:
            e = sys.exc_info()[0]
            self.logexception(1)
            etxt = 'pollenc exception %s (%s)' % (e.__class__, e)
            self.handleError(etxt)

        return

    def sendErrorStats(self):
        rmmonitor.send_error_event({ 'tags': ["pollenc_server_job"] }, \
            'pollenc_server exception', \
            'pollenc_server txn failed')
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

    rmmonitor = RiemannMonitor.RiemannMonitor()
    REDIS_HOST = config.redis['host']
    REDIS_PORT = config.redis['port']
    TCP_HOST = socket.getfqdn() # on aws this is internal name, which works.
    TCP_PORT = config.pollenc_tcp['port']

    syslog.syslog(syslog.LOG_INFO, 'service starting using redis host %s:%s' % ((REDIS_HOST, REDIS_PORT))) 
    
    address = ((TCP_HOST, TCP_PORT)) 
    server = PollencServer(address, PollencRequestHandler)

    server.serve_forever()

    syslog.syslog(syslog.LOG_INFO, 'service stopping')

    server.socket.close()

