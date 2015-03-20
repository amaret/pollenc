''' Pollen Cloud Compiler Client Util Functions '''

import zipfile
import os
import shutil
import base64

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

def unzip(src):
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

def unpack(workobj, outdir):
    ''' extract bin data from json'''
    # unpack response
    b64 = workobj['content']['source']
    zipbytes = base64.b64decode(b64)

    origpath = os.getcwd()
    os.chdir(outdir)
    unzip(zipbytes)
    os.chdir(origpath)

