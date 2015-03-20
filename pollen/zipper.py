# pylint: disable=bad-whitespace
# Copyright 2014 Amaret Inc. All rights reserved.
''' Pollen Cloud Compiler Zip Util'''

from pollen.scrlogger import ScrLogger
from pollen.utils import rmfile
from pollen.utils import rmdir
from pollen.utils import get_bundle_name
import shutil
import zipfile
import os
import glob
import datetime

class Zipper(object):
    ''' Pollen Cloud Compiler Zip Util'''

    def __init__(self, workzip, bundle_paths, workname, cbundle):
        self.log          = ScrLogger("DEBUG")
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
        rmfile(self.workzip)
        zip_ = zipfile.ZipFile(self.workzip, 'w')
        self._make_bundle_zip(zip_)
        self._make_c_zip(zip_)
        zip_.close()
        self.log.debug("File preparation took %s seconds." %
                       str((datetime.datetime.now() -
                            starttime).total_seconds()))

    def unzip(self, src):
        ''' unpack the response from the server'''
        tmpzip = 'a.zip'
        binfile = open(tmpzip, 'wb')
        binfile.write(src)
        binfile.close()

        with zipfile.ZipFile(tmpzip) as zfile:
            for member in zfile.namelist():
                # passing exec permission thru zip did not work
                # anyhow flags for exec are os dependent.
                # this is a hack but should work okay.
                zfile.extract(member, '.')
                name = member.split('-', 1)
                if len(name) > 1:
                    if name[1] == "prog.out":
                        os.chmod(member, 0755)
        rmfile(tmpzip)


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
            rmdir(self.tmpdir)
            bundle_name = get_bundle_name(src)
            if bundle_name not in self.bundle_names:
                self.bundle_names.append(bundle_name)
            shutil.copytree(src, self.tmpdir + '/' + bundle_name)
            self._zip_dir(self.tmpdir, zip_)
            rmdir(self.tmpdir)

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
            rmdir(self.tmpdir)
            os.mkdir(self.tmpdir)
            shutil.copytree(src, self.tmpdir + '/cbundle/')
            self._zip_dir(self.tmpdir, zip_)
            rmdir(self.tmpdir)

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

