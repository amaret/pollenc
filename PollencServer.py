#!/usr/bin/python2
import sys
import SocketServer
import syslog
import socket
import threading

class PollencRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        # Echo the back to the client
        data = self.request.recv(1024)
        cur_thread = threading.currentThread()
        response = '%s: %s' % (cur_thread.getName(), data)
        self.request.send(response)
        return

class PollencServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass

class PollencServerx(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    
    def __init__(self, server_address, handler_class=PollencRequestHandler):
        SocketServer.TCPServer.__init__(self, server_address, handler_class)
        return

    def server_activate(self):
        SocketServer.TCPServer.server_activate(self)
        return

    def serve_forever(self):
	print 'Server loop running'
        while True:
            self.handle_request()
        return

    def handle_request(self):
        return SocketServer.TCPServer.handle_request(self)

    def verify_request(self, request, client_address):
        return SocketServer.TCPServer.verify_request(self, request, client_address)

    def process_request(self, request, client_address):
        return SocketServer.TCPServer.process_request(self, request, client_address)

    def server_close(self):
        return SocketServer.TCPServer.server_close(self)

    def finish_request(self, request, client_address):
        return SocketServer.TCPServer.finish_request(self, request, client_address)

    def close_request(self, request_address):
        return SocketServer.TCPServer.close_request(self, request_address)

if __name__ == '__main__':

    print 'Server starting...'
    address = ('localhost', 2323)
    server = PollencServer(address, PollencRequestHandler)
    ip, port = server.server_address # find out what port we were given

    server.serve_forever()

    print '... Server stoping'
    # Clean up
    server.socket.close()

