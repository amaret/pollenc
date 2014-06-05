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

def rmfile(f):
    try:
            os.remove(f)
    except:
            pass

def rmdir(d):
    try:
            shutil.rmtree(d)
    except:
            pass


class Pollenc:

  def __init__ (self, args):
    self.bundleNames = []
    self.env = args.env
    self.prn = args.prn
    self.args = args
    self.aid = str(os.getpid()) + '_' + str(random.randint(1, 10000))
    self.workname = 'pollenc_' + self.aid
    self.workzip = '/tmp/' + self.workname + '_src.zip'

    # Using redis for now
    self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    self.qName = 'POLLEN_CLC_0_1'      

  def makezip(self):
       rmfile(self.workzip)
       self.makeBundleZip()

  def zipBundles(self, zip, paths):
        tmpdir = '/tmp/' + self.workname
        print "client tmpdir %s" % tmpdir
        for src in paths:
            if src.find('*')!=-1 or src.find('?')!=-1:
                wildcardLst = glob.glob(src)
                if len(wildcardLst) > 0:
                    self.zipBundles(zip, wildcardLst) #recurse for wildcard
                    continue
            if not os.path.exists(src):
                self.bundleNames.append(src)
                continue #system bundle
            rmdir(tmpdir)
            bundleName = self.getBundleName(src)
            if bundleName in self.bundleNames:
                continue #dupe -i
            self.bundleNames.append(bundleName)
            shutil.copytree(src, tmpdir + '/' + bundleName)
            self.zipdir(tmpdir, zip)
            rmdir(tmpdir)

  def makeBundleZip(self):
        zip = zipfile.ZipFile(self.workzip, 'w')
        print "client bundles %s" % self.args.bundles
        if self.args.bundles != None:
            self.zipBundles(zip, self.args.bundles)
            zip.close()

  def unzip(self,src): 
      tmpzip = 'a.zip' 
      try: 
          binfile = open(tmpzip, 'wb')
          binfile.write(src)
          binfile.close()
          z = zipfile.ZipFile(tmpzip)
          z.extractall('.')
          rmfile(tmpzip)
      except Exception, e:
          print("argh! %s" % (e))


  def filenameOk(self, file):
        if file.endswith('.zip'):
            return False
        if file.endswith('stderr'):
            return False
        if file.endswith('stdout'):
            return False
        if file.endswith('.out'):
            return False
        if file.endswith('.hex'):
            return False
        return True

  def zipdir(self, path, zip):
        origpath = os.getcwd()
        os.chdir(path)
        namelist = ''
        for root, dirs, files in os.walk('.'):
            for file in files:
                if self.filenameOk(file):
                    namelist += root + '/'+ file + ' '
                    zip.write(os.path.join(root, file))
        #if self.getVerbose() > 0:
        #    print('preparing %s' % (namelist))
        os.chdir(origpath)

  def printStdErr(self):
        for root, dirs, files in os.walk(self.args.outdir):
            for f in files:
                if f.endswith('err'):
                    print 'msgs found in stderr from server:'
                    with open(root + '/' + f, 'r') as fin:
                        print fin.read()


  def getBundleName(self, path):
        abspath = os.path.abspath(path)
        (r, m) = os.path.split(abspath)
        return m

  def getData(self):
	file = open(self.workzip, "rb")
        data = ''
        while True:
            chunk = file.read(1024)
            if not chunk:
                break  # EOF
            data += chunk
        file.close()
        return data

  def getRelToTmpDirName(self):
        abspath = os.path.abspath(self.args.entry)
        (r, m) = os.path.split(abspath)
        l = abspath.split("/")
        llen = len(l)
        if llen < 3:
            raise Exception('filename must be in <bundle>/<package>')
        r = l[llen -3] + '/' + l[llen -2] + '/' + l[llen -1]
        return r

  def sendCompileRequest(self):    
    tid = hashlib.sha1(str(time.time()) + '-' + self.args.token).hexdigest()    
    b64data = base64.b64encode(self.getData())

    self.reply = 'clc_response_' + self.aid + '_' + tid

    jsonobj = {
      'compiler': self.args.toolchain,
      'tid': tid,
      'aid': self.aid,
      'reply': self.reply,
      'type': 'request', 
      'service': 'compile', 
      'bundles': self.bundleNames,
      'env': self.env,
      'prn': self.prn,
      'user': {
        'token': self.args.token, 
        'id': 0, 
        'name': 'None'
      },
      'content' :  {
        'source':  b64data, 
        'entry': self.getRelToTmpDirName(),
        'mcu': self.args.mcu
      }
    }

    print "Sending compile request:"
    print "client aid %s" % self.aid
    self.redis.lpush(self.qName, json.dumps(jsonobj))
    print jsonobj


  def run(self):
    self.makezip()
    print "Pollenc running.."
    self.sendCompileRequest()

    while True:
      response = self.redis.brpop(keys=[self.reply], timeout=600);
      if ( not response or not len(response) == 2) :
        raise Exception('bad response from clc: %s' % (response))
        print "error"

      workobj   = json.loads(response[1])
      if workobj['type'] != 'response': 
          print ('%s' % (workobj['content']['source'])) 
          continue
      if workobj['content']['error'] != 'None': 
          print ('pollenc error! %s' % (workobj['content']['error'])) 
          return
      break

    rmfile(self.workzip)

    b64 = workobj['content']['source']
    zipbytes = base64.b64decode(b64)
    origpath = os.getcwd()
    os.chdir(self.args.outdir)
    self.unzip(zipbytes)
    os.chdir(origpath)
    print "\nPollenc done. Build output in " + self.args.outdir
    self.printStdErr() #look for stderr and play msgs



if __name__ == "__main__":
  
  parser = argparse.ArgumentParser()

  # The host and port arguments are for later. Right now pollenc is using redis not sockets. 
  parser.add_argument('--host', dest='host', action='store', help='wind.io host', default="passage.wind.io")
  parser.add_argument('--port', dest='port', action='store', help='wind.io port', default=2323, type=int)

  # The token argument is for later. It will be a user specified token that identifies them. 
  parser.add_argument('--token', dest='token', action='store', help='user credential', required=False)

  ###
  # Here we need to collect the rest of the arguments that a user may provide on the commandline for the 
  # translator and compiler. For example, the input bundles included, the output directory, any cflags, 
  # other flags, etc.
  ####
  group = parser.add_mutually_exclusive_group()

  parser.add_argument('-b', '--bundles', dest='bundles',  nargs='*', action='store', help="list of pollen bundles. Paths prefixed with '@' are on server, the rest will be uploaded.", required=False)
  parser.add_argument('-i', '--include', dest='includes',  nargs='*', action='store', help='list of c files to be uploaded to server', required=False)
  group.add_argument('-t', '--toolchain', dest='toolchain', action='store', help='toolchain (compiler)', required=False, choices = ['avr-gcc', "msp430-gcc", "arm-gcc", "localhost-gcc"])
  parser.add_argument('--mcu', dest='mcu', action='store', help='microcontroller', required=False)
  parser.add_argument('--cflags', dest='cflags', action='store', help='extra options to pass to C compiler', required=False)
  parser.add_argument('-e', '--entry', dest='entry',  action='store', help='top level pollen file (entry point)', required=True)
  parser.add_argument('--env', dest='env', action='store', help='pollen module used for pollen.environment', required=False)
  parser.add_argument('--prn', dest='prn', action='store', help='pollen module that will implement the print protocol', required=False)
  parser.add_argument('-o', '--out',   dest='outdir', action='store', help='output dir', default='./build')
  group.add_argument('--props', dest='props', action='store', help='properties file (for toolchain compiler and options)', required=False)


  args = parser.parse_args()

  if args.host == None:
    args.host = ""

  if args.token == None:
    args.token = 'TOKEN-' + str(random.randint(1, 10000))

  args.translateOnly = False
  if (args.props == None and args.toolchain == None):
	  args.translateOnly = True

  args.build = not args.translateOnly

  if not args.translateOnly and args.mcu == None:
      print("If toolchain is specified then -mcu <microcontroller> must also be specified") 
      sys.exit(0)

  if args.translateOnly and args.mcu != None:
      print("If -mcu <microcontroller> is specified then toolchain must also be specified")
      sys.exit(0)

  if os.path.exists(args.outdir):
      rmdir(args.outdir)
  os.mkdir(args.outdir)

  args.entry = os.path.abspath(args.entry)
  (p, m) = os.path.split(args.entry)
  (bname, p) = os.path.split(p)
  if args.bundles == None:
     args.bundles = []
  if bname not in args.bundles:
     args.bundles.append(bname)

  # if the environment module is local put its bundle in bundle list
  if args.env != None: 
      if args.env[0] != '@': # not on the server
          args.env = os.path.abspath(args.env) 
          (p1, m) = os.path.split(args.env) 
          (bname, p2) = os.path.split(p1) 
          args.env = p2 + "/" + m
          if bname not in args.bundles: 
              args.bundles.append(bname)

  # if the print module impl is local put its bundle in bundle list
  if args.prn != None: 
      if args.prn[0] != '@': # not on the server
          args.prn = os.path.abspath(args.prn) 
          (p1, m) = os.path.split(args.prn) 
          (bname, p2) = os.path.split(p1) 
          args.prn = p2 + "/" + m
          if bname not in args.bundles: 
              args.bundles.append(bname)

  if not os.path.exists(args.entry):
     print "Module " + args.entry + " not found"
     sys.exit()

  Pollenc(args).run() 

