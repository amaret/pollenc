#!/usr/bin/env python
import SocketServer
import threading
import redis
import argparse
import syslog
import json

rdis = ''
ERROR_MSG = '{\"tid\": \"0\", \"aid\": \"0\", \"type\": \"response\", \"service\": \"compile\", \"user\": {\"id\": \"0\", \"name\": \"None\"}, \"project\": {\"id\": \"0\", \"name\": \"None\"}, \"content\" : {\"content\": \"None\", \"filename\": \"None\", \"error\": \"%s\" }}'

class PollencRequestHandler(SocketServer.BaseRequestHandler):

    def getQName(self):
        return 'CLC_MSP430_1_0'
        #return 'CLC_ARDUINO_1_0'

    def write(self, dstr):
	    rdis.lpush(self.getQName(), dstr);
    
    def read(self, replyQueue):
        response = rdis.brpop(keys=[replyQueue], timeout=30);
        if ( not response or not len(response) == 2) :
            raise Exception('bad response from clc: %s' % (response))
        return response[1]

    def validateToken(self, token):
        #todo:
        return token == 'rustyisacowboy'
    
    def handle(self):
        data = ''
        data = self.request.recv(32768)

        dataobj = json.loads(data)
        token = dataobj["user"]["token"]
        if not self.validateToken(token):
            syslog.syslog(syslog.LOG_INFO, 'pollenc rejecting token %s' % (token))
            emsg =  ERROR_MSG % ('bad token')
            self.request.send(emsg)
            return

        syslog.syslog(syslog.LOG_INFO, 'pollenc request handler invoked for token %s' % (token))
	    #todo: len headers and a watchdog
        #while True:
        #    chunk = self.request.recv(1024)
        #    if not chunk:
        #        break
        #    data += chunk
        cur_thread = threading.currentThread()
        responseQueue = 'POLLENC_REPLYTO_QUEUE_%s_%s' % (cur_thread.getName(), dataobj["user"]["name"])
        dataobj["reply"] = responseQueue
        self.write(json.dumps(dataobj))

        while True:
            response = self.read(responseQueue)
            self.request.send(response)
            dataobj = json.loads(response)
            if dataobj['type'] != 'response':
                continue
            break
        return


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
    
    address = ('localhost', 2323)
    server = PollencServer(address, PollencRequestHandler)

    server.serve_forever()

    syslog.syslog(syslog.LOG_INFO, 'service stopping')

    server.socket.close()

