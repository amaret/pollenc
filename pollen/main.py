# Copyright Amaret, Inc 2011-2015. All rights reserved.

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

    try:
        cmd, pargs = parse()

        net = WebSocker(pargs.host, pargs.port)     # instantiate comm

        if cmd is 'build':

            prep             = Preparer(pargs)      # instantiate packager
            request          = prep.prepare()       # prepare request
            success, workobj = net.talk(request)    # send request get response
            if success:
                LOG.trace(workobj)
                utils.unpack(workobj, pargs.outdir) # unpack response
                LOG.info("Build complete. Output files are in %s" %
                         (pargs.outdir))

        elif cmd is 'login':
            prep             = LoginPreparer(pargs) # instantiate packager
            request          = prep.prepare()       # prepare request
            success, workobj = net.talk(request)    # send request get response
            if success:
                token = workobj['content']['new_token']
                utils.save_token(token)
                LOG.debug("Storing new token. %s" % token)

                url   = 'https://github.com/login/oauth/authorize'

                url   = 'https://github.com/login/oauth/authorize'
                cid   = os.getenv('CLIENT_ID', '6828e1c35f58e155e145')
                url   = url + '?client_id=' + cid
                cburl = os.getenv('OAUTH_CB', 'http://pollen.amaret.com/auth')
                url  = url + '&redirect_uri=' + cburl
                url = url + '&scope=' + 'repo,user'
                url  = url + '&state=' + token

                LOG.notice('Trying to open a browser.')
                LOG.notice('If a browser window ' \
                           'does not open, copy the following into your ' \
                           'browser to proceed:')
                LOG.notice(url)
                LOG.info('')
                webbrowser.open(url, new=0, autoraise=True)

    # pylint: disable=broad-except
    except Exception, ex:
        LOG.error(ex)
        import traceback
        trace = traceback.format_exc()
        LOG.trace(trace)

