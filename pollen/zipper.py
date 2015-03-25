# Copyright Amaret, Inc 2011-2015. All rights reserved.
# pylint: disable=bad-whitespace
# Copyright 2014 Amaret Inc. All rights reserved.
''' Pollen Cloud Compiler Zip Util'''

import shutil
import zipfile
import os
import glob
import datetime

from pollen import utils
from pollen.scrlogger import ScrLogger


class Zipper(object):
    ''' Pollen Cloud Compiler Zip Util'''

    def __init__(self, workzip, bundle_paths, workname, cbundle):
        self.log          = ScrLogger()
        self.workzip      = workzip
        self.bundle_paths = bundle_paths
        self.cbundle      = cbundle
        self.bundle_names  = []
        self.tmpdir       = '/tmp/' + workname

    def zip(self):
        ''' create the file'''
        self.log.info("\nPreparing files...", 0)
        self.log.debug("Work directory: " + self.tmpdir)
        self.log.debug("Bundle directories (%s): %s" %
                       (str(len(self.bundle_paths) - 1),
                        str(self.bundle_paths[1:])))

        starttime = datetime.datetime.now()
        utils.rmfile(self.workzip)
        zip_ = zipfile.ZipFile(self.workzip, 'w')
        self._make_bundle_zip(zip_)
        self._make_c_zip(zip_)
        zip_.close()
        self.log.debug("File preparation took %s seconds." %
                       str((datetime.datetime.now() -
                            starttime).total_seconds()))

    def _zip_bundles(self, zip_, paths):
        ''' add local bundles to the zip and maintain list of bundle names'''

        for src in paths:
            if src.find('*') != -1 or src.find('?') != -1:
                wildcards = glob.glob(src)
                if len(wildcards) > 0:
                    self._zip_bundles(zip_, wildcards)  # recurse for wildcard
                    continue
            if not os.path.exists(src):
                self.bundle_names.append(src)
                continue  # system bundle
            utils.rmdir(self.tmpdir)
            bundle_name = utils.get_bundle_name(src)
            if bundle_name not in self.bundle_names:
                self.bundle_names.append(bundle_name)
            shutil.copytree(src, self.tmpdir + '/' + bundle_name)
            self._zip_dir(self.tmpdir, zip_)
            utils.rmdir(self.tmpdir)

    def _make_bundle_zip(self, zip_):
        ''' add local bundles to the zip and maintain list of bundle names'''
        if self.bundle_paths is not None:
            for src in self.bundle_paths:
                if src[0] == '@':  # not on the server
                    continue
                _, _, _ = os.walk(src).next()  # todo: ejs??

            self._zip_bundles(zip_, self.bundle_paths)

    def _make_c_zip(self, zip_):
        ''' add c dirs to zip'''
        ptmp = []
        if self.cbundle is None:
            return
        else:
            for des in self.cbundle:
                if des[0] != '@':  # not on the server
                    ptmp.append(des)

        if len(ptmp) > 0:
            self.log.debug("C directory included: %s" % str(ptmp))

        for src in ptmp:
            utils.rmdir(self.tmpdir)
            os.mkdir(self.tmpdir)
            shutil.copytree(src, self.tmpdir + '/cbundle/')
            self._zip_dir(self.tmpdir, zip_)
            utils.rmdir(self.tmpdir)

    def _filename_ok(self, file_):
        ''' some files should not be sent to the server'''
        if file_.endswith('.zip'):
            return False
        if file_.endswith('stderr'):
            return False
        if file_.endswith('stdout'):
            return False
        if file_.endswith('.out'):
            return False
        if file_.endswith('.hex'):
            return False
        return True

    def _zip_dir(self, path, zip_):
        ''' zip!'''
        origpath = os.getcwd()
        os.chdir(path)
        for root, _, files in os.walk('.'):
            for file_ in files:
                if self._filename_ok(file_):
                    zip_.write(os.path.join(root, file_))
        os.chdir(origpath)

