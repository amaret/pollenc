''' Pollen Cloud Compiler Client Util Functions '''

import os
import shutil

def get_data(filename):
    ''' read bin file into memory'''
    file_ = open(filename, "rb")
    data = ''
    while True:
        chunk = file_.read(1024)
        if not chunk:
            break  # EOF
        data += chunk
    file_.close()
    return data


def get_rel_to_temp_dir_name(filepath):
    ''' calculate bundle name for filepath'''
    if filepath is None:
        return None
    abspath = os.path.abspath(filepath)
    lname = abspath.split("/")
    llen = len(lname)
    if llen < 3:
        raise Exception('filename must be in <bundle>/<package>')
    rec = lname[llen - 3] + '/' + lname[llen - 2] + '/' + lname[llen - 1]
    return rec


def get_bundle_name(path):
    ''' parse bundle name from a file path'''
    abspath = os.path.abspath(path)
    (_, bname) = os.path.split(abspath)
    return bname


def rmfile(file_):
    ''' remove file if it exists'''
    try:
        os.remove(file_)
    except OSError:
        pass


def rmdir(dir_):
    ''' remove dir if it exists'''
    try:
        shutil.rmtree(dir_)
    except OSError:
        pass


