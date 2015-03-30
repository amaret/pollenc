# Copyright Amaret, Inc 2011-2015. All rights reserved.
# pylint: disable=missing-docstring
# pylint: disable=bad-whitespace
''' Pollen Cloud Compiler Client '''

import os
import shutil
import hashlib
import time
import base64

from pollen.scrlogger import ScrLogger
from pollen.zipper import Zipper
from pollen import utils

CLC_CONSTANTS = {
    'MAX_MSG_SIZE': 1000000,
}


class Preparer(object):
    # pylint: disable=too-many-instance-attributes

    def __init__(self, args_):
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        self.args = args_

        self.log = ScrLogger()

        self.jsonobj = ""

        self.bundle_paths  = []
        self.trace         = args_.trace  # superset of verbose output
        self.verbose       = True if args_.verbose and not args_.trace else \
                             False
        self.token         = utils.token()
        self.aid           = hashlib.sha1(self.token).hexdigest()
        self.workname      = 'pollenc_' + self.aid
        self.pollen_env    = '/tmp/' + self.workname + '_env'
        self.pollen_prn    = '/tmp/' + self.workname + '_prn'
        self.pollen_entry  = '/tmp/' + self.workname + '_entry'
        self.workzip       = '/tmp/' + self.workname + '_src.zip'
        self.props         = self.args.props is not None

        if len(self.args.cbundle) > 0:
            if self.args.cflags is None:
                self.args.cflags = "\"-Icbundle\""
            else:
                self.args.cflags = "\"" + self.args.cflags + " -Icbundle \""

        self.prn = self.args.prn
        self.env = self.args.env

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

        (pname1, mod)  = os.path.split(self.args.entry)
        (bpath, pname) = os.path.split(pname1)
        (_, bname)     = os.path.split(bpath)

        if os.path.exists(self.pollen_entry):
            utils.rmdir(self.pollen_entry)

        os.makedirs(self.pollen_entry + '/' + bname + '/' + pname)
        onlyfiles = [os.path.join(pname1, f) for f in os.listdir(pname1)
                     if os.path.isfile(os.path.join(pname1, f))]
        for fil in onlyfiles:
            shutil.copy2(fil, self.pollen_entry + '/' + bname + '/' + pname)
        # if a props files is to be used, copy it to entry directory with
        # name 'props'
        if self.props and os.path.isfile(self.args.props):
            shutil.copy2(self.args.props, self.pollen_entry + '/' + bname +
                         '/' + pname + '/props')
        self.args.entry = self.pollen_entry + '/' + bname + '/' + \
            pname + '/' + mod
        self.bundle_paths.append(self.pollen_entry + '/' + bname)

        for src in self.args.bundle_paths:
            self.bundle_paths.append(src)

    def _prepare_env_mod(self):
        # if the environment module is local put its bundle in bundle list
        if self.args.env is not None:
            if self.args.env[0] != '@':  # not on the server
                self.args.env  = os.path.abspath(self.args.env)
                (pname1, mod)        = os.path.split(self.args.env)
                (bpath, pname) = os.path.split(pname1)
                (_, bname)     = os.path.split(bpath)
                bname_path = self.pollen_env + '/' + bname
                self.bundle_paths.append(bname_path)
                if os.path.exists(self.pollen_env):
                    utils.rmdir(self.pollen_env)
                pname_path = bname_path + '/' + pname
                os.makedirs(pname_path)
                target = pname_path + '/' + mod + '.p'
                shutil.copy2(self.args.env + '.p', target)
                self.env = pname_path + '/' + mod

    def _prepare_print_mod(self):
        # if the print module impl is local put its bundle in bundle list
        if self.args.prn is not None:
            if self.args.prn[0] != '@':  # not on the server
                self.args.prn  = os.path.abspath(self.args.prn)
                (pname1, mod)        = os.path.split(self.args.prn)
                (bpath, pname) = os.path.split(pname1)
                (_, bname)     = os.path.split(bpath)
                bname_path = self.pollen_prn + '/' + bname
                self.bundle_paths.append(bname_path)
                if os.path.exists(self.pollen_prn):
                    utils.rmdir(self.pollen_prn)
                pname_path = bname_path + '/' + pname
                os.makedirs(pname_path)
                shutil.copy2(self.args.prn + '.p', pname_path + '/' +
                             mod + '.p')
                self.prn = pname_path + '/' + mod

    def _prep_request(self, bundle_names):
        token = utils.token()
        tid = hashlib.sha1(str(time.time()) + '-' +
                           token).hexdigest()
        b64data = base64.b64encode(utils.get_data(self.workzip))

        jsonobj = {'compiler': self.args.toolchain,
                   'tid'     : tid,
                   'aid'     : self.aid,
                   'type'    : 'request',
                   'service' : 'compile',
                   'bundles' : bundle_names,
                   'env'     : utils.get_rel_to_temp_dir_name(self.env),
                   'prn'     : utils.get_rel_to_temp_dir_name(self.prn),
                   'trace'   : self.trace or self._verbose() == 3,
                   'props'   : self.props,
                   'cflags'  : self.args.cflags,
                   'xferstarttime': 0,  # self.ntpTime() don't use this fcn.
                   'user': {'token': token,
                            'id': 0,
                            'name': 'None'},
                   'content': {'source':  b64data,
                               'entry':
                                   utils.get_rel_to_temp_dir_name(
                                       self.args.entry),
                               'mcu': self.args.mcu},
                   'times': {'pcc_read_client_job'   : 0,
                             'pcc_total_time'        : 0,

                             'redis_push_for_worker' : 0,
                             'redis_wait_for_worker' : 0,
                             'redis_wait_for_pcc'    : 0,

                             'worker_prepare_job'    : 0,
                             'worker_run_pollen'     : 0,
                             'worker_run_gcc'        : 0,
                             'worker_run_objcopy'    : 0,
                             'worker_finalize_job'   : 0}}

        self.log.info("\nBuilding %s.p ..." % jsonobj['content']['entry'])
        self.log.trace(jsonobj)

        self.jsonobj = jsonobj

    def _clean(self):
        if os.path.exists(self.args.outdir):
            if os.path.abspath(self.args.outdir) == os.getcwd():
                msg = "Option error: -o output directory cannot be current \
                       directory"
                raise Exception(msg)
            utils.rmdir(self.args.outdir)
        os.mkdir(self.args.outdir)

    def prepare(self):

        self._clean()
        self._prepare_bundle()
        self._prepare_env_mod()
        self._prepare_print_mod()

        zipper = Zipper(self.workzip, self.bundle_paths, self.workname,
                        self.args.cbundle)
        zipper.zip()
        self._prep_request(zipper.bundle_names)
        utils.rmfile(self.workzip)

        return self.jsonobj

