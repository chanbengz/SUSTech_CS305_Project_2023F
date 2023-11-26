from argparse import ArgumentParser
from threading import Thread
from HTTPServer.TCPServer import Server
from HTTPServer.RequestHandle import *
import time, socket, uuid, base64, re, mimetypes, pathlib, json, signal
import sqlite3 as sql

parser = ArgumentParser()
parser.add_argument('--ip', '-i', type=str)
parser.add_argument('--port', '-p', type=int)
args = parser.parse_args()
PORT = args.port or 8080
IP = args.ip or ''

class RequestHandler:
    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server
        self.handle()

    def handle(self):
        con = self.request
        start_time = time.time()
        while True:
            # Receive data
            recv_data = bytes()
            try:
                con.settimeout(timeout - time.time() + start_time)
                while True:
                    data = con.recv(1024)
                    recv_data += data
                    if len(data) < 1024:
                        break
                if recv_data == b'':
                    continue
            except socket.timeout:
                con.close()
                return # Timeout

            print(recv_data.decode())
            print('-----------------------------------')
            method, path, protocol, headers, msgdata = parse_request(recv_data.decode('utf-8'))
            if protocol.upper() != http_version:
                con.sendall(parse_header(headers, 505))
                continue

            # Authentication
            user_database = sql.connect('Database/users.db')
            cookie_database = sql.connect('Database/cookies.db')
            if 'Cookie' not in headers:
                try:
                    if 'Authorization' in headers:
                        name, passwd = base64.b64decode(headers['Authorization'].strip('Basic ')).decode().split(':')
                        user_passwd = ''
                        for result in user_database.execute(f"select passwd from users where name = '{name}';"):
                            user_passwd = result[0]
                        if user_passwd == passwd:
                            session_id = uuid.uuid4().hex
                            cookie_database.execute(f"insert into cookies values ('{name}', '{session_id}', {int(time.time())});")
                            cookie_database.commit()
                            headers['Set-Cookie'] = 'session-id=' + session_id
                        else:
                            raise
                    else:
                        raise
                except:
                    con.sendall(parse_header(headers, 401) + b'WWW-Authenticate: Basic realm="Authorization Required"\r\n\r\n')
                    continue
            else:
                duration = 3600
                for result in cookie_database.execute(f"select * from cookies where session_id = '{headers['Cookie'].strip('session-id=')}';"):
                    duration = int(time.time()) - result[2]
                if duration > 3600:
                    cookie_database.execute(f"delete from cookies where session_id = '{headers['Cookie'].strip('session-id=')}';")
                    con.sendall(parse_header(headers, 401) + b'WWW-Authenticate: Basic realm="Authorization Required"\r\n\r\n')
                    continue
            user_database.close()
            cookie_database.close()

            # Process request
            if method.upper() == 'GET':
                con.sendall(process_get(path, headers))
            elif method.upper() == 'POST':
                con.sendall(process_post(path, headers, msgdata))
            elif method.upper() == 'HEAD':
                con.sendall(process_head(path, headers))
            else:
                con.sendall(parse_header(headers, 501).encode('utf-8'))
            if headers.get('Connection').lower() == 'close':
                con.close()
                return

if __name__ == "__main__":
    server = Server((IP, PORT), RequestHandler)
    Thread(target=server.serve_forever).start()
