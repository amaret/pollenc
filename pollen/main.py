# Copyright 2014 Amaret Inc. All rights reserved.

''' Pollen Cloud Compiler Client '''

# pylint: disable=bad-whitespace
import webbrowser
import os

from pollen import utils
from pollen.scrlogger import ScrLogger
from pollen.preparer import Preparer
from pollen.login_preparer import LoginPreparer
from pollen.websocker import WebSocker
from pollen.argparser import parse

LOG = ScrLogger()

def main():
    '''main entry point'''

    cmd, pargs = parse()

    net = WebSocker(pargs.host, pargs.port)     # instantiate comm

    if cmd is 'build':

        prep             = Preparer(pargs)      # instantiate request packager
        request          = prep.prepare()       # prepare request
        success, workobj = net.talk(request)    # send request and get response
        if success:
            LOG.trace(workobj)
            utils.unpack(workobj, pargs.outdir) # unpack response
            LOG.info("Build complete. Output files are in %s" % (pargs.outdir))

    elif cmd is 'login':
        prep             = LoginPreparer(pargs) # instantiate request packager
        request          = prep.prepare()       # prepare request
        success, workobj = net.talk(request)    # send request and get response
        if success:
            token = workobj['content']['new_token']
            utils.save_token(token)
            LOG.debug("Storing new token. %s" % token)
            url = 'https://github.com/login/oauth/authorize'
            client_id = os.getenv('CLIENT_ID', 'b4081d536c6fa61025f6')
            url = url + '?client_id=' + client_id
            cburl = os.getenv('OAUTH_CB', 'http://pollen.amaret.com/auth')
            url = url + '&redirect_uri=' + cburl
            #url = url + '&scope=' + 'repo'
            url = url + '&state=' + token
            webbrowser.open(url, new=0, autoraise=True)

