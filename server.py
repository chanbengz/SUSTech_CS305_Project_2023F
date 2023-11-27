from argparse import ArgumentParser
from threading import Thread
from HTTPServer.TCPServer import ThreadingServer
from HTTPServer.RequestHandle import *
import time, socket, uuid, base64
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
        username = ''
        while True:
            # Receive data
            recv_data = bytes()
            try:
                if timeout - time.time() + start_time <= 0:
                    raise socket.timeout
                con.settimeout(timeout - time.time() + start_time)
                while True:
                    data = con.recv(1024)
                    recv_data += data
                    if len(data) < 1024:
                        con.settimeout(None)
                        break
                if recv_data == b'':
                    continue
            except socket.timeout:
                con.close()
                return # Timeout

            print(recv_data.decode())
            print('-----------------------------------')
            method, path, protocol, headers, msgdata = parse_request(recv_data.decode('utf-8').strip('\r\n'))
            path, parameters = parse_path(path)
            
            if protocol.upper() != http_version:
                con.sendall(parse_header(headers, 505))
                continue
            
            # Send Icon
            if path == '/favicon.ico':
                con.sendall(process_icon(headers))
                continue

            headers['Authorization'] = 'Basic Y2xpZW50MToxMjM=' # debug
            # Authentication and Cookie
            user_database = sql.connect('Database/users.db')
            cookie_database = sql.connect('Database/cookies.db')
            try:
                if 'Cookie' not in headers:
                    if 'Authorization' in headers:
                        username, passwd = base64.b64decode(headers['Authorization'].strip('Basic ')).decode().split(':')
                        user_passwd = ''
                        for result in user_database.execute(f"select passwd from users where name = '{username}';"):
                            user_passwd = result[0]
                        if user_passwd == passwd:
                            session_id = str(uuid.uuid4())
                            cookie_database.execute(f"insert into cookies values ('{username}', '{session_id}', {int(time.time())});")
                            cookie_database.commit()
                            headers['Set-Cookie'] = 'session-id=' + session_id
                        else:
                            raise
                    else:
                        raise
                else:
                    duration = 3600
                    session_id = headers['Cookie'].split('=')[1]
                    for result in cookie_database.execute(f"select * from cookies where session_id = '{session_id}';"):
                        username = result[0]
                        duration = int(time.time()) - result[2]
                    if duration >= 3600:
                        username = ''
                        cookie_database.execute(f"delete from cookies where session_id = '{session_id}';")
                        raise
            except:
                headers['WWW-Authenticate'] = 'Basic realm="Authorization Required"'
            finally:
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
    server = ThreadingServer((IP, PORT), RequestHandler)
    Thread(target=server.serve_forever).start()
