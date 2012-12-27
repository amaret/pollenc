#!/usr/bin/env python

# Copyright 2012 Amaret Inc. All rights reserved.

import argparse
import sys
import json
import glob
import ClcBase
import zipfile
import os
import syslog
import base64
import random
import redis
import datetime

defaults = {

    'REDIS_HOST' : '127.0.0.1:6379',
    }

class ClcClient(ClcBase.ClcBase):

    def __init__ (self, userid, txnid, filename, partnum):
        ClcBase.ClcBase.__init__(self, defaults, userid, txnid)
        self.filename = filename
        self.partnum = partnum
        self.replyTo = 'clc_response_' + self.userid + '_' + self.txnid
        self.workzip = './ClcClient' + str(os.getpid()) + '_' + str(random.randint(1, 10000)) + '_src.zip'
        (rhost, rport) = self.getHostPort(self.cfg.get('options', 'REDIS_HOST'))
        self.rdis = redis.Redis(host=rhost, port=rport)


    def getQName(self):
        if '430' in self.filename:
            return 'CLC_MSP430_1_0'
        else:
            return 'CLC_ARDUINO_1_0'

    def zipdir(self, path, zip):
      syslog.syslog(syslog.LOG_DEBUG, '%s %s zip dir %s' % (self.userid, self.txnid, path))
      for root, dirs, files in os.walk(path):
        for file in files:
          if not file.endswith('.zip'):
            zip.write(os.path.join(root, file))


    def makezip(self, filename):
        syslog.syslog(syslog.LOG_DEBUG, '%s %s makezip %s' % (self.userid, self.txnid, filename))
        zip = zipfile.ZipFile(filename, 'w')
        self.zipdir('.', zip)
        zip.close()

    def sendzip(self):
        syslog.syslog(syslog.LOG_DEBUG, '%s %s sendzip' % (self.userid, self.txnid))
        file = open(self.workzip, "rb")
        data = ''
        while True:
            chunk = file.read(1024)
            if not chunk: 
                break  # EOF
            data += chunk
        file.close()
        b64data = base64.b64encode(data)
        #{ 'tid': tid,   // transaction id
        #  'aid': chan,    // correlation id (its the client's channel name)
        #  'reply': PROJECT_SERVICE_1_0, // name of queue to reply to, if reply expected
        #  'type': 'transaction',  // type should be transaction
        #  'user':    {'id': 'eb3b865f3473806fe6373f31537d5a7304c81bcd', 'name': 'Amichi Amar'},
        #  'project': {'id': 'a4ba6460bba3a6fb6cad9d007c12cf4bae75836c', 'name': 'LightBead'}
        #  'content' :  {'source':  [base64 encoded zip file], 'filename': [name of file to compile] }
        #}

        jsonstr = '{ \"tid\": \"%s\", \"aid\": \"%s\", \"reply\": \"%s\", \"type\": \"request\", \"service\": \"compile\", \"user\": {\"id\": \"%s\", \"name\": \"%s\"}, \"project\": {\"id\": \"%s\", \"name\": \"%s\"}, \"content\" :  {\"source\":  \"%s\", \"filename\": \"%s\", \"partnum\": \"%s\" } }' % (self.txnid, 42, self.replyTo, 12345678, self.userid, 'myproj123', 'myproj', b64data, self.filename, self.partnum)
        self.rdis.lpush(self.getQName(), jsonstr);

        syslog.syslog(syslog.LOG_DEBUG, '%s %s sent zip to clc service' % (self.userid, self.txnid))

    def run(self):

        starttime = datetime.datetime.now()

        syslog.syslog(syslog.LOG_DEBUG, '%s %s started' % (self.userid, self.txnid))

        self.makezip(self.workzip)

        self.sendzip()

        while True:
          response = self.rdis.brpop(keys=[self.replyTo], timeout=30);
          if ( not response or not len(response) == 2) :
            raise Exception('bad response from clc: %s' % (response))

          workobj   = json.loads(response[1])
          if workobj['type'] != 'response':
              #print ('got log msg: %s\n' % (response[1]))
              continue

          os.remove(self.workzip)

          content   = workobj['content']
          src       = content['content']

          stoptime = datetime.datetime.now()
          dur = stoptime - starttime
          syslog.syslog(syslog.LOG_DEBUG, '%s %s duration microseconds %i' % (self.userid, self.txnid, dur.microseconds))

          return src


if __name__ == "__main__":

    userid = None
    txnid = None
    filename = None
    partnum = None

    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--filename', dest='filename', action='store', help='src filename')
        parser.add_argument('-p', '--partnum',  dest='partnum', action='store', help='partnum')
        parser.add_argument('-i', '--userid',   dest='userid', action='store', help='logging header')
        parser.add_argument('-x', '--txnid',    dest='txnid', action='store', help='logging header')
        args = parser.parse_args()
        userid = args.userid
        txnid = args.txnid
        filename = args.filename
        partnum = args.partnum

    if filename == None:
        filename = "Blink.ino"

    r = ClcClient(os.getlogin(), str(os.getpid()), filename, partnum).run() 
    print(r)

