# pylint: disable=missing-docstring
# pylint: disable=bad-whitespace
# pylint: disable=invalid-name
''' Pollen Cloud Compiler Client '''

import os
import random
import shutil
import hashlib
import time
import base64

from pollen.scrlogger import ScrLogger
from pollen.zipper import Zipper
from pollen.utils import rmfile
from pollen.utils import get_data
from pollen.utils import get_rel_to_temp_dir_name
from pollen.utils import rmdir


CLC_CONSTANTS = {
    'MAX_MSG_SIZE': 1000000,
}


class Preparer(object):
    # pylint: disable=too-many-instance-attributes

    def __init__(self, args_, net):
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        self.net = net
        self.args = args_

        self.log = ScrLogger("DEBUG")

        self.jsonobj = ""

        self.bundle_paths  = []
        self.trace         = args_.trace  # superset of verbose output
        self.verbose       = True if args_.verbose and not args_.trace else \
                             False
        self.aid           = str(os.getpid()) + '_' + \
                             str(random.randint(1, 10000))
        self.reply         = 'POLLENC_REPLYTO_QUEUE_%s' % self.aid
        self.workname      = 'pollenc_' + self.aid
        self.pollen_env    = '/tmp/' + self.workname + '_env'
        self.pollen_prn    = '/tmp/' + self.workname + '_prn'
        self.pollen_entry  = '/tmp/' + self.workname + '_entry'
        self.workzip       = '/tmp/' + self.workname + '_src.zip'
        self.translateOnly = self.args.translateOnly
        self.props         = self.args.props is not None

        if len(self.args.cbundle) > 0:
            if self.args.cflags is None:
                self.args.cflags = "\"-Icbundle\""
            else:
                self.args.cflags = "\"" + self.args.cflags + " -Icbundle \""

        self.prn = self.args.prn
        self.env = self.args.env

        self._prepare_bundle()
        self._prepareEnvModule()
        self._preparePrintModule()

    def _verbose(self):
        if self.args.vvverbose is True:
            return 3
        if self.args.vverbose is True:
            return 2
        if self.args.verbose is True:
            return 1
        return 0

    def _prepare_bundle(self):
        # Set up the bundle_paths. Create tmp directories for
        # entry, print module, environment to avoid copying all files in the
        # bundles for each of these to the server. We copy only what is in the
        # package of each of these. Also transmit the server local bundle
        # names.

        (p1, m) = os.path.split(self.args.entry)
        (bpath, pname) = os.path.split(p1)
        (_, bname) = os.path.split(bpath)

        if os.path.exists(self.pollen_entry):
            rmdir(self.pollen_entry)

        os.mkdir(self.pollen_entry)
        os.mkdir(self.pollen_entry + '/' + bname)
        os.mkdir(self.pollen_entry + '/' + bname + '/' + pname)
        onlyfiles = [os.path.join(p1, f) for f in os.listdir(p1)
                     if os.path.isfile(os.path.join(p1, f))]
        for f in onlyfiles:
            shutil.copy2(f, self.pollen_entry + '/' + bname + '/' + pname)
        # if a props files is to be used, copy it to entry directory with
        # name 'props'
        if self.props and os.path.isfile(self.args.props):
            shutil.copy2(self.args.props, self.pollen_entry + '/' + bname +
                         '/' + pname + '/props')
        self.args.entry = self.pollen_entry + '/' + bname + '/' + \
            pname + '/' + m
        self.bundle_paths.append(self.pollen_entry + '/' + bname)

        for src in self.args.bundle_paths:
            self.bundle_paths.append(src)

    def _prepareEnvModule(self):
        # if the environment module is local put its bundle in bundle list
        if self.args.env is not None:
            if self.args.env[0] != '@':  # not on the server
                self.args.env  = os.path.abspath(self.args.env)
                (p1, m)        = os.path.split(self.args.env)
                (bpath, pname) = os.path.split(p1)
                (_, bname)     = os.path.split(bpath)
                bnamePath = self.pollen_env + '/' + bname
                self.bundle_paths.append(bnamePath)
                if os.path.exists(self.pollen_env):
                    rmdir(self.pollen_env)
                pnamePath = bnamePath + '/' + pname
                os.makedirs(pnamePath)
                target = pnamePath + '/' + m + '.p'
                shutil.copy2(self.args.env + '.p', target)
                self.env = pnamePath + '/' + m

    def _preparePrintModule(self):
        # if the print module impl is local put its bundle in bundle list
        if self.args.prn is not None:
            if self.args.prn[0] != '@':  # not on the server
                self.args.prn  = os.path.abspath(self.args.prn)
                (p1, m)        = os.path.split(self.args.prn)
                (bpath, pname) = os.path.split(p1)
                (_, bname)     = os.path.split(bpath)
                bnamePath = self.pollen_prn + '/' + bname
                self.bundle_paths.append(bnamePath)
                if os.path.exists(self.pollen_prn):
                    rmdir(self.pollen_prn)
                pnamePath = bnamePath + '/' + pname
                os.makedirs(pnamePath)
                shutil.copy2(self.args.prn + '.p', pnamePath + '/' + m + '.p')
                self.prn = pnamePath + '/' + m

    def printStdErr(self):
        for root, _, files in os.walk(self.args.outdir):
            for f in files:
                if f.endswith('err'):
                    if self._verbose() == 3:
                        print '\nMessages from server:'
                        with open(root + '/' + f, 'r') as fin:
                            print fin.read()
                            return
                    if self._verbose() > 0:
                        print '\nMessages from server found in ' + str(root) \
                            + '/' + str(f)

    def printStdOut(self):
        for root, _, files in os.walk(self.args.outdir):
            for file_ in files:
                if file_.endswith('stdout'):
                    with open(root + '/' + file_, 'r') as fin:
                        nr_of_lines = sum(1 for line in fin)
                        if nr_of_lines > 1:
                            print '\nHost phase print output:\n'
                            fin.close()
                            with open(root + '/' + file_, 'r') as fin:
                                print fin.read()

    def _prep_request(self, bundle_names):
        tid = hashlib.sha1(str(time.time()) + '-' +
                           self.args.userid).hexdigest()
        b64data = base64.b64encode(get_data(self.workzip))

        jsonobj = {'compiler': self.args.toolchain,
                   'tid'     : tid,
                   'aid'     : self.aid,
                   'reply'   : self.reply,
                   'type'    : 'request',
                   'service' : 'compile',
                   'bundles' : bundle_names,
                   'env'     : get_rel_to_temp_dir_name(self.env),
                   'prn'     : get_rel_to_temp_dir_name(self.prn),
                   'trace'   : self.trace or self._verbose() == 3,
                   'props'   : self.props,
                   'cflags'  : self.args.cflags,
                   'xferstarttime': 0,  # self.ntpTime() don't use this fcn.
                   'user': {'token': self.args.userid,
                            'id': 0,
                            'name': 'None'},
                   'content': {'source':  b64data,
                               'entry':
                                   get_rel_to_temp_dir_name(self.args.entry),
                               'mcu': self.args.mcu},
                   'times': {'pcc_read_client_job':  0,
                             'pcc_total_time':  0,

                             'redis_push_for_worker':  0,
                             'redis_wait_for_worker': 0,
                             'redis_wait_for_pcc': 0,

                             'worker_prepare_job': 0,
                             'worker_run_pollen': 0,
                             'worker_run_gcc': 0,
                             'worker_run_objcopy': 0,
                             'worker_finalize_job': 0}}

        self.log.info("\nBuilding %s.p ..." % jsonobj['content']['entry'])
        self.log.trace(jsonobj)

        self.jsonobj = jsonobj

    def prepare(self):

        zipper = Zipper(self.workzip, self.bundle_paths, self.workname,
                        self.args.cbundle)
        zipper.zip()
        self._prep_request(zipper.bundle_names)

    def run(self):

        # todo: move this stuff into Net impls
        # todo: rename Comppile.py to Prepare.py

        # flow
        #
        #   process args into a conf obj
        #
        #   create Preparer
        #   create Zipper
        #   create Socker (soon to be WebSocker)
        #
        #   run Preparer (to make tmp stuff)
        #   run Zipper (to make zip file)
        #   run (Web)Socker (to send and receive)
        #

        # this stuff onConnect
        self.net.write(self.jsonobj)

        # this stuff onMessage
        while True:

            workobj = self.net.read()
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

        # this stuff onDone
        rmfile(self.workzip)
        self.log.trace(workobj)
        b64      = workobj['content']['source']
        zipbytes = base64.b64decode(b64)

        # ejs TODO move into main and unzip
        # ejs TODO move into main and unzip
        # ejs TODO move into main and unzip
        origpath = os.getcwd()
        os.chdir(self.args.outdir)
        Zipper(self.workzip, self.bundle_paths, self.workname,
               self.args.cbundle).unzip(zipbytes)
        os.chdir(origpath)

        # ejs TODO move into main
        # ejs TODO move into main
        # ejs TODO move into main
        self.log.info("Build complete. Output files are in " +
                      self.args.outdir)
        if self._verbose() == 3:
            self.log.info("Build timing data can be found in the output \
                    directory in file timing_data.csv.")
            self.log.info("(All times are in milliseconds.)")

