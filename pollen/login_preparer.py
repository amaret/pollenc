# Copyright Amaret, Inc 2011-2015. All rights reserved.
# pylint: disable=missing-docstring
# pylint: disable=bad-whitespace
''' Pollen Cloud Compiler Client '''

import hashlib
import time
import os
import random

from pollen.scrlogger import ScrLogger
from pollen import utils

LOGGER = ScrLogger()

class LoginPreparer(object):

    def __init__(self, args_):

        self.args = args_
        self.aid = str(os.getpid()) + '_' + str(random.randint(1, 10000))
        self.jsonobj = {}

    def _prep_request(self):
        token = utils.anon_token()
        tid = hashlib.sha1(str(time.time()) + '-' +
                           token).hexdigest()

        jsonobj = {'tid'     : tid,
                   'aid'     : self.aid,
                   'type'    : 'request',
                   'service' : 'login',
                   'user': {'token': token,
                            'id': 0,
                            'name': 'None'},}

        self.jsonobj = jsonobj

    def prepare(self):

        self._prep_request()

        return self.jsonobj

