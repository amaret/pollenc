#!/usr/bin/env python

# Copyright 2014 Amaret Inc. All rights reserved.

import sys
import subprocess
import shutil
import shlex
import argparse #cmdline overrides configrgs
import json
import zipfile
import os
import base64
import random
import time
import hashlib
import redis

REDIS_HOST = "redbis.wind.io"
REDIS_PORT = 6379



class Pollenc:

  def __init__ (self, args):
    self.args = args
    self.aid = str(os.getpid()) + '_' + str(random.randint(1, 10000))
    self.workname = 'pollenc_' + self.aid
    self.workzip = '/tmp/' + self.workname + '_src.zip'

    # Using redis for now
    self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    self.qName = 'POLLEN_CLC_0_1'      


  def sendCompileRequest(self):    
    tid = hashlib.sha1(str(time.time()) + '-' + self.args.token).hexdigest()    
    jsonobj = {
      'compiler': 'pollen_avr_gcc', 
      'tid': tid,
      'aid': self.aid,
      'reply': 'dummy', 
      'type': 'request', 
      'service': 'compile', 
      'user': {
        'token': self.args.token, 
        'id': 0, 
        'name': 'None'
      },
      'content' :  {
        'source':  "b64data", 
        'filename': "SOME FILE NAME",
        'mcu': "SOME_MCU"
      }
    }

    print "Sending compile request:"
    self.redis.lpush(self.qName, json.dumps(jsonobj))
    print jsonobj


  def run(self):
    print "Pollenc running.."
    self.sendCompileRequest()
    print "Pollenc done..."



if __name__ == "__main__":
  
  parser = argparse.ArgumentParser()

  # The host and port arguments are for later. Right now pollenc is using redis not sockets. 
  parser.add_argument('--host', dest='host', action='store', help='wind.io host', default="passage.wind.io")
  parser.add_argument('--port', dest='port', action='store', help='wind.io port', default=2323, type=int)

  # The token argument is for later. It will be a user specified token that identifies them. 
  parser.add_argument('-t', '--token', dest='token', action='store', help='user credential', required=False)

  ###
  # Here we need to collect the rest of the arguments that a user may provide on the commandline for the 
  # translator and compiler. For example, the input bundles included, the output directory, any cflags, 
  # other flags, etc.
  ####
  parser.add_argument('--cFlags', dest='cFlags', action='store', help='options to pass to C compiler', required=False)
  parser.add_argument('--env', dest='env', action='store', help='pollen module used for pollen.environment', required=False)
  parser.add_argument('--props', dest='props', action='store', help='properties file', required=False)
  parser.add_argument('--avr-gcc', dest='avr-gcc', action='store', help='avr target, gcc compiler', required=False)
  parser.add_argument('--efm32-gcc', dest='efm32-gcc', action='store', help='efm32 target, gcc compiler', required=False)
  parser.add_argument('--localhost-gcc', dest='localhost-gcc', action='store', help='localhost target, gcc compiler', required=False)
  parser.add_argument('--msp430-gcc', dest='msp430-gcc', action='store', help='msp430 target, gcc compiler', required=False)

  parser.add_argument('-e', '--entry', dest='entry',  action='store', help='pollen file entry point', required=True)
  parser.add_argument('-o', '--out',   dest='outdir', action='store', help='output dir', default='./build')


  args = parser.parse_args()

  if args.host == None:
    args.host = ""

  if args.token == None:
    args.token = 'TOKEN-' + str(random.randint(1, 10000))

  Pollenc(args).run() 

