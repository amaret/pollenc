# Copyright 2014 Amaret Inc. All rights reserved.

''' Pollen Cloud Compiler Client '''

# pylint: disable=bad-whitespace

from pollen import utils
from pollen.scrlogger import ScrLogger
from pollen.preparer import Preparer
from pollen.websocker import WebSocker
from pollen.argparser import parse

LOG = ScrLogger()

def main():
    '''main entry point'''

    pargs = parse()

    #
    # begin main program
    #

    net     = WebSocker(pargs.host, pargs.port) # instantiate comm
    prep    = Preparer(pargs)                # instantiate request packager
    request = prep.prepare()                 # prepare request
    workobj = net.talk(request)              # send request and get response

    LOG.trace(workobj)
    utils.unpack(workobj, pargs.outdir)            # unpack response

    LOG.info("Build complete. Output files are in %s" % (pargs.outdir))

