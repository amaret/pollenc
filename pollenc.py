#!/usr/bin/env python

# Copyright 2012 Amaret Inc. All rights reserved.

import argparse
import sys
import json
import glob
import zipfile
import os
import base64
import random
import redis
import datetime

defaults = {

    'REDIS_HOST' : '127.0.0.1:6379',
    }

class ClcClient:

    def __init__ (self, usertoken, filename, partnum):
        self.usertoken = usertoken
        self.filename = filename
        self.partnum = partnum
        self.workzip = './pollenc' + str(os.getpid()) + '_' + str(random.randint(1, 10000)) + '_src.zip'
        self.initRdis() 

    #
    # begin comm
    #
    # todo: replace with socket
    # todo: for PollenService, this is the handler code except user 'name' is usertoken and must be validated
    # todo: for PollenService, get environment out of json and use in getQName
    #
    def initRdis(self):
	self.replyTo = 'pollenc_response_' + usertoken
        rhost = "localhost"
        rport = 6379
        self.rdis = redis.Redis(host=rhost, port=rport)

    def getQName(self):
        return 'CLC_MSP430_1_0'
        #return 'CLC_ARDUINO_1_0'

    def write(self, dstr):
	self.rdis.lpush(self.getQName(), dstr);
    
    def read(self):
        response = self.rdis.brpop(keys=[self.replyTo], timeout=30);
        if ( not response or not len(response) == 2) :
          raise Exception('bad response from clc: %s' % (response))
  	return response[1]
    #
    # end comm
    #

    # presumes path is the parent dir to the 'code' dir
    def zipdir(self, path, zip):
      for root, dirs, files in os.walk(path):
        for file in files:
          if not file.endswith('.zip'):
            zip.write(os.path.join(root, file))


    def makezip(self, filename):
        zip = zipfile.ZipFile(filename, 'w')
        self.zipdir('.', zip)
        zip.close()

    def sendzip(self):
        file = open(self.workzip, "rb")
        data = ''
        while True:
            chunk = file.read(1024)
            if not chunk: 
                break  # EOF
            data += chunk
        file.close()
        b64data = base64.b64encode(data)

        jsonstr = '{ \"tid\": \"%s\", \"aid\": \"%s\", \"reply\": \"%s\", \"type\": \"request\", \"service\": \"compile\", \"user\": {\"id\": \"%s\", \"name\": \"%s\"}, \"project\": {\"id\": \"%s\", \"name\": \"%s\"}, \"content\" :  {\"source\":  \"%s\", \"filename\": \"%s\", \"partnum\": \"%s\" } }' % (0, 42, self.replyTo, 12345678, self.usertoken, 'myproj123', 'myproj', b64data, self.filename, self.partnum)
        
	self.write(jsonstr)

    def run(self):

        starttime = datetime.datetime.now()

        self.makezip(self.workzip)

        self.sendzip()

        while True:
	  r = self.read()
          workobj   = json.loads(r)
          if workobj['type'] != 'response':
              #print ('got log msg: %s\n' % (r))
              continue

          os.remove(self.workzip)

          content   = workobj['content']
          src       = content['content']

          stoptime = datetime.datetime.now()
          dur = stoptime - starttime

          return src


if __name__ == "__main__":

    if len(sys.argv) > 1:

        parser = argparse.ArgumentParser()
        
	parser.add_argument('-f', '--filename', dest='filename', action='store', help='src filename')
        parser.add_argument('-p', '--partnum',  dest='partnum', action='store', help='partnum')
        parser.add_argument('-t', '--usertoken',   dest='usertoken', action='store', help='user credential')
        
	args = parser.parse_args()
        
	usertoken = args.usertoken
        filename = args.filename
        partnum = args.partnum

    if partnum == None:
        raise Exception('no --partnum specified')

    if filename == None:
        raise Exception('no --filename specified')

    if usertoken == None:
        raise Exception('no --usertoken specified')

    r = ClcClient(usertoken, filename, partnum).run() 
    print(r)

