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
        headers = self.parse_request(recv_data.decode('utf-8'))
        con.send(b'HTTP/1.1 200 OK\r\n')
        con.close()
    
    def parse_request(request):
        request = request.split('\r\n')
        request = request[0].split(' ')
        method, path, protocol = request
        


if __name__ == "__main__":
    server = Server((IP, PORT), RequestHandler)
    Thread(target=server.serve_forever).start()