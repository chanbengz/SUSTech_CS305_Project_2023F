from argparse import ArgumentParser
from threading import Thread
from HTTPServer.TCPServer import Server
import time, re, mimetypes, sys, datetime, pathlib, uuid, base64, json, signal, io, os
import sqlite3 as sql

parser = ArgumentParser()
parser.add_argument('--ip', '-i', type=str)
parser.add_argument('--port', '-p', type=int)
args = parser.parse_args()
PORT = args.port or 8080
IP = args.ip or ''

home_page = open('public/index.html', 'rb').read()
icon = open('public/favicon.ico', 'rb').read()
cookie_database = sql.connect('Database/cookies.db')
user_database = sql.connect('Database/users.db')
http_version = 'HTTP/1.1'
status_code = {
    200: 'OK',
    206: 'Partial Content',
    301: 'Redirect',
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    416: 'Range Not Satisfiable',
    501: 'Not Implemented',
    505: 'HTTP Version Not Supported',
}

class RequestHandler:
    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server
        self.maxconnect = 100
        self.timeout = 120
        self.handle()

    def handle(self):
        con = self.request
        start_time = time.time()
        auth = True
        while True:
            recv_data = bytes()
            while True:
                data = con.recv(1024)
                recv_data += data
                if len(data) < 1024:
                    break
            print(recv_data.decode())
            print('-----------------------------------')
            method, path, protocol, headers, msgdata = self.parse_request(recv_data.decode('utf-8'))
            if protocol.upper() != 'HTTP/1.1':
                con.sendall(self.parse_header(headers, 505).encode('utf-8'))
                continue
            if not auth:
                try:
                    if 'Authorization' in headers:
                        name, passwd = base64.b64decode(headers['Authorization']).split(':')
                        user_passwd = ''
                        for i in user_database.execute(f"select passwd from users where name = '{name}'"):
                            user_passwd = i[0]
                        if user_passwd == passwd:
                            auth = True
                        else:
                            raise
                    else:
                        raise
                except:
                    con.sendall(self.parse_header(headers, 401).encode('utf-8'))
                    continue

            if method.upper() == 'GET':
                con.sendall(self.process_get(path, headers))
            elif method.upper() == 'POST':
                self.process_post(path, headers, msgdata)
            elif method.upper() == 'HEAD':
                con.sendall(self.process_head(path, headers))
            else:
                con.sendall(self.parse_err_header(headers, 501).encode('utf-8'))
            if headers.get('Connection').lower() == 'close':
                break
        con.close()
    
    def parse_header(self, headers, code):
        res_header = ''
        res_header += http_version + ' ' + str(code) + ' ' + status_code[code] + '\r\n'
        res_header += 'Server: ' + 'Python HTTP Server' + '\r\n'
        res_header += 'Date: ' + datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT') + '\r\n'
        if 'Connection' in headers:
            if headers['Connection'].lower() == 'keep-alive':
                res_header += 'Keep-Alive: timeout=' + str(self.timeout) + ', max=' + str(self.maxconnect) + '\r\n'
                res_header += 'Connection: keep-alive\r\n'
            elif headers['Connection'].lower() == 'close':
                res_header += 'Connection: close\r\n'
        return res_header
    
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
        if path == '/favicon.ico':
            data = icon
        else:
            data = home_page
        return self.process_head(path, headers) + b'\r\n' + data


    def process_post(self, path, headers, msgdata):
        pass

    def process_head(self, path, headers):
        res_header = self.parse_header(headers, 200)
        if path == '/favicon.ico':
            data = icon
            res_header += 'Content-Type: image/x-icon\r\n'
        else:
            data = home_page
            res_header += 'Content-Type: text/html\r\n'
        res_header += 'Content-Length: ' + str(len(data)) + '\r\n'
        return res_header.encode('utf-8')

if __name__ == "__main__":
    server = Server((IP, PORT), RequestHandler)
    Thread(target=server.serve_forever).start()
