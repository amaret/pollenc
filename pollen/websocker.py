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
        ''' read and write'''

        result = asyncio.Future()

        class PollenProtocol(WebSocketClientProtocol):
            # pylint: disable=too-many-ancestors
            '''requries python2.7ish due to trollius coroutine syntax'''

            def onConnect(self, response):
                print "Server connected: {0}".format(response.peer)

            # @trollius.COROutine
            @asyncio.coroutine
            def onOpen(self):
                self.sendMessage(json.dumps(request).encode('utf8'))

            def onMessage(self, payload, isBinary):
                workobj = json.loads(payload.decode('utf8'))
                if workobj['type'] == 'userlog':
                    LOG.ulog(workobj)
                    return
                if workobj['type'] != 'response':
                    return
                if workobj['content']['error'] != 'None':
                    print 'pollenc error! %s' % (workobj['content']['error'])

                result.set_result(workobj)

            def onClose(self, wasClean, code, reason):
                print "WebSocket connection closed: {0}".format(reason)

        LOG.debug("starting ws conn to %s : %d" % (self.host, self.port))
        factory = WebSocketClientFactory("wss://%s:%d" %
                                         (self.host, self.port),
                                         debug=False)
        factory.protocol = PollenProtocol

        loop = asyncio.get_event_loop()
        coro = loop.create_connection(factory, self.host, self.port)
        loop.run_until_complete(coro)
        ret = loop.run_until_complete(result)
        loop.close()
        return ret

