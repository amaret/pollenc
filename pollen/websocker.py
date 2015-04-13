# Copyright Amaret, Inc 2011-2015. All rights reserved.
''' Pollen Cloud Compiler Socket Protocol Impl '''
# pylint: disable=bad-whitespace
import logging
logging.basicConfig()

from autobahn.asyncio.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory
import json
import trollius as asyncio

from pollen.scrlogger import ScrLogger

BUFSZ = 1024

LOG = ScrLogger()


class WebSocker(object):
    ''' Pollen Cloud Compiler Socket Protocol Impl '''

    def __init__(self, host, port):

        self.host = host
        self.port = port

    def talk(self, request):
        ''' read and write.  returns success, result'''

        result = asyncio.Future()

        class PollenProtocol(WebSocketClientProtocol):
            # pylint: disable=too-many-ancestors
            '''requries python2.7ish due to trollius coroutine syntax'''

            def onConnect(self, response):
                LOG.debug("Server connected: {0}".format(response.peer))

            # @trollius.COROutine
            @asyncio.coroutine
            def onOpen(self):
                self.sendMessage(
                    json.dumps(request,
                               separators=(',', ':')).encode('utf8'))

            def _quit(self, success, workobj):
                ''' quit '''
                LOG.trace("WebSocket _quit")
                result.set_result((success, workobj))
                self.sendClose()

            def onMessage(self, payload, isBinary):
                LOG.trace("WebSocket onMessage")
                msg = payload.decode('utf8')
                workobj = json.loads(msg)

                if 'type' not in workobj:
                    LOG.error("bad response: %s", msg)
                    self._quit(False, workobj)
                    return

                if 'content' not in workobj:
                    LOG.error("bad response: %s", msg)
                    self._quit(False, workobj)
                    return

                if workobj['type'] == 'userlog':
                    LOG.trace("WebSocket onMessage userlog")
                    LOG.ulog(workobj)
                    return
                if workobj['type'] != 'response':
                    LOG.trace("WebSocket onMessage response")
                    return
                if 'error' in workobj['content'] \
                        and workobj['content']['error'] != 'None' \
                        and workobj['content']['error'] is not None:
                    LOG.trace("WebSocket onMessage error")
                    self._quit(False, workobj)
                    LOG.error("pollenc error! %s" %
                              workobj['content']['error'])
                    return

                self._quit(True, workobj)

            def onClose(self, wasClean, code, reason):
                LOG.debug("WebSocket connection closed: {0}".format(reason))

        wsurl = "ws://%s:%d/wspollen" % (self.host, self.port)
        LOG.debug("starting ws conn to %s" % (wsurl))
        factory = WebSocketClientFactory(wsurl, debug=False)
        factory.protocol = PollenProtocol

        loop = asyncio.get_event_loop()
        coro = loop.create_connection(factory, self.host, self.port)
        loop.run_until_complete(coro)
        ret = loop.run_until_complete(result)
        loop.close()
        return ret[0], ret[1]
