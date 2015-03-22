# Copyright 2014 Amaret Inc. All rights reserved.

''' Pollen Cloud Compiler Client Arg Parser'''

# pylint: disable=bad-whitespace

import argparse
import os
import sys
import random


POLLENC_TCP = {
    'interface': 'pcc1.amaret.com',
    'port': 80,
}


def parse():
    ''' create arg object'''
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    parser = argparse.ArgumentParser()

    parser.add_argument('-b', '--bundle', dest='bundle_paths', action='append',
                        help="pollen bundle. Paths prefixed with '@' are on \
                        server, the rest will be uploaded.",
                        required=False)

    help_str = ('Path prefixed with "@" is on server, else this is the ' +
                'local root of subtree of c files to be uploaded to server. ' +
                'Note root of local subtree uploaded to the cloud will ' +
                'be \'cbundle\'.')
    parser.add_argument('-cb', '--cbundle', dest='cbundle', action='append',
                        help=help_str, required=False)

    parser.add_argument('--cflags=', dest='cflags', action='store',
                        help='quoted string containing extra options to pass \
                        to C compiler.',
                        required=False)

    help_str = ('pollen module used for pollen.environment. ' +
                'Path prefixed with "@" is on server, else will be uploaded.')
    parser.add_argument('-e', '--environment', dest='env', action='store',
                        help=help_str, required=False)

    tcp_host = POLLENC_TCP['interface']
    help_str = ('The Pollen Cloud Compiler gateway to connect to.  Default  \
                 is %s' % tcp_host)
    parser.add_argument('--host', dest='host', action='store',
                        help=help_str, default=tcp_host)

    parser.add_argument('-m', '--mcu', dest='mcu', action='store',
                        help='microcontroller', required=False)

    help_str = ('output dir. Warning: will be emptied before use.')
    parser.add_argument('-o', '--out', dest='outdir', action='store',
                        help=help_str, default='./build')

    tcp_port = POLLENC_TCP['port']
    help_str = ('The Pollen Cloud Compiler gateway port to connect to.  \
                 Default is %d' % tcp_port)
    parser.add_argument('--port', dest='port', action='store',
                        help=help_str, default=tcp_port, type=int)

    parser.add_argument('--props', dest='props', action='store',
                        help='properties file (for toolchain compiler and \
                        options).',
                        required=False)

    help_str = 'pollen module that will implement the print protocol. ' \
        + 'Path prefixed with "@" is on server, else will be uploaded.'
    parser.add_argument('-p', '--print-module', dest='prn', action='store',
                        help=help_str, required=False)

    parser.add_argument('-t', '--toolchain', dest='toolchain', action='store',
                        help='toolchain (compiler).', required=False,
                        choices=['avr-gcc', "arm-none-eabi-gcc", "efm32-gcc",
                                 "localhost-gcc"])

    parser.add_argument('--trace', dest='trace', action='store_true',
                        help=argparse.SUPPRESS)

    # The userid argument is for later. It will be a user specified userid
    # that identifies them.
    parser.add_argument('-u', '--user', dest='userid', action='store',
                        help='user credential', required=False)

    parser.add_argument('-v', '--verbose', dest='verbose',
                        action='store_true', help='verbose output')

    parser.add_argument('-vv', '--vverbose', dest='vverbose',
                        action='store_true', help='very verbose output')

    parser.add_argument('-vvv', '--vvverbose', dest='vvverbose',
                        action='store_true', help='very very verbose output')

    parser.add_argument('entry', nargs='?', action='store',
                        help='top level pollen file (entry point). Qualify ' +
                        'with bundle and package.')

    pargs = parser.parse_args()

    if len(sys.argv) == 1:     # no args: print help
        parser.print_help()
        sys.exit(0)

    if pargs.cbundle is None:
        pargs.cbundle = []

    if pargs.bundle_paths is None:
        pargs.bundle_paths = []

    if pargs.host is None:
        pargs.host = ""

    # ejs TODO look for stored guid
    if pargs.userid is None:
        pargs.userid = 'TOKEN-' + str(random.randint(1, 10000))

    if pargs.vverbose is True:
        pargs.verbose = True
    if pargs.vvverbose is True:
        pargs.verbose = True
        pargs.vverbose = True

    pargs.translateOnly = False
    if pargs.props is None and pargs.toolchain is None:
        pargs.translateOnly = True

    if pargs.translateOnly and pargs.mcu is not None:
        print "Option error: If --mcu option is specified then -t \
                (toolchain) must also be specified"
        sys.exit(1)

    if not pargs.translateOnly and pargs.toolchain != "localhost-gcc" and  \
            pargs.mcu is None:
        print("Option error: --mcu option is required with toolchain " +
              pargs.toolchain)
        sys.exit(1)

    if pargs.toolchain == "localhost-gcc" and pargs.mcu is not None:
        print "Option error: --mcu option should not be specified with \
                toolchain " + pargs.toolchain
        sys.exit(1)

    if pargs.translateOnly:
        pargs.toolchain = "localhost-gcc"

    if not os.path.exists(pargs.entry):
        print "Module " + pargs.entry + " not found"
        sys.exit()

    pargs.entry = os.path.abspath(pargs.entry)
    if pargs.entry.endswith('.p'):
        pargs.entry = pargs.entry[:-2]
    if pargs.prn is not None:
        if pargs.prn.endswith('.p'):
            pargs.prn = pargs.prn[:-2]
    if pargs.env is not None:
        if pargs.env.endswith('.p'):
            pargs.env = pargs.env[:-2]

    return pargs

