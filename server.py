from argparse import ArgumentParser
from threading import Thread
from HTTPServer.TCPServer import Server
import re, mimetypes, sys, datetime, pathlib, uuid, base64, json, signal, io, os
import sqlite3 as sql

parser = ArgumentParser()
parser.add_argument('--ip', '-i', type=str)
parser.add_argument('--port', '-p', type=int)
args = parser.parse_args()
PORT = args.port or 8080
IP = args.ip or ''

home_page = open('public/index.html', 'rb').read()
cookie_database = sql.connect('cookies.db')

class RequestHandler:
    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server
        self.handle()

    def handle(self):
        con = self.request
        recv_data = bytes()
        while True:
            data = con.recv(1024)
            recv_data += data
            if len(data) < 1024:
                break
        method, path, protocol, headers, msgdata = self.parse_request(recv_data.decode('utf-8'))
        if protocol.upper() != 'HTTP/1.1':
            con.send(b'HTTP/1.1 505 HTTP Version Not Supported\r\n')
            con.close()
            return
        if method.upper() == 'GET':
            self.process_get(path, headers)
        elif method.upper() == 'POST':
            self.process_post(path, headers, msgdata)
        elif method.upper() == 'HEAD':
            self.process_head(path, headers)
        else:
            con.send(b'HTTP/1.1 501 Not Implemented\r\n')
            con.close()
            return
        con.send(b'HTTP/1.1 200 OK\r\n')
        con.close()
    
    def parse_request(self, request):
        request = request.split('\r\n')
        method, path, protocol = request[0].split(' ')
        data = request[-1]
        result = dict()
        for i in range(1, len(request) - 1):
            if request[i] == '':
                continue
            key, value = request[i].split(': ')
            result[key] = value
        return method, path, protocol, result, data
    
    def process_get(self, path, headers):
        pass

    def process_post(self, path, headers, msgdata):
        pass

    def process_head(self, path, headers):
        pass

if __name__ == "__main__":
    server = Server((IP, PORT), RequestHandler)
    Thread(target=server.serve_forever).start()
