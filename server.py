from argparse import ArgumentParser
from threading import Thread
from HTTPServer.TCPServer import ThreadingServer
from HTTPServer.RequestHandle import *
import time, socket

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
            method, path, protocol, headers, msgdata = parse_request(recv_data.decode('utf-8').strip('\r\n'))
            
            if protocol.upper() != http_version:
                con.sendall(parse_header(headers, 505))
                continue
            
            # Send Icon
            if path == '/favicon.ico':
                con.sendall(process_icon(headers))
                continue

            # Authentication and Cookie
            headers = authenticate(headers)

            # Process request
            path, parameters = parse_path(path)
            try:
                if path.strip('/') == command[0]:
                    if method.upper() == 'GET':
                        raise
                    con.sendall(process_upload(parameters['path'], headers, msgdata))
                elif path.strip('/') == command[1]:
                    if method.upper() == 'POST':
                        raise
                    con.sendall(process_delete(parameters['path'], headers))
                else:
                    if method.upper() == 'POST':
                        raise
                    sustech = 'SUSTech-HTTP' in parameters and parameters['SUSTech-HTTP'] == '1'
                    head = method.upper() == 'HEAD'
                    process_download(con, path.strip('/'), headers, sustech, head)
            except:
                con.sendall(parse_header(headers, 405) + b'\r\n')
            
            if headers['Connection'].lower() == 'close':
                con.close()
                return

if __name__ == "__main__":
    server = ThreadingServer((IP, PORT), RequestHandler)
    Thread(target=server.serve_forever).start()
