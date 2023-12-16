from argparse import ArgumentParser
from threading import Thread
from HTTPServer.TCPServer import ThreadingServer
from HTTPServer.RequestHandle import *
import time, socket
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Util.Padding import unpad, pad

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
        self.cipher = None
        self.decryptor = None
        self.handle()

    def handle(self):
        con = self.request
        
        if encrypt:
            rsa_key = RSA.generate(2048)
            con.sendall(rsa_key.public_key().export_key())
            key = PKCS1_OAEP.new(rsa_key).decrypt(con.recv(1024))
            iv = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F'
            self.cipher = AES.new(key, AES.MODE_CBC, iv)
            self.decryptor = AES.new(key, AES.MODE_CBC, iv)
        
        start_time = time.time()
        print(con.getpeername())
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
            
            if encrypt:
                recv_data = unpad(self.decryptor.decrypt(recv_data), 16, style='pkcs7')
            print(recv_data.decode())
            method, path, protocol, headers, msgdata = parse_request(recv_data.strip(b'\r\n'))
            
            if protocol.upper() != http_version:
                self.send(parse_header(headers, 505))
                continue
            
            # Send Icon
            if path == '/favicon.ico':
                self.send(process_icon(headers))
                continue

            # Authentication and Cookie
            headers = authenticate(headers)

            # Process request
            path, parameters = parse_path(path)

            if path.strip('/') == command[0]:
                if method.upper() == 'GET':
                    self.send(parse_header(headers, 405) + b'\r\n')
                    continue
                self.send(process_upload(parameters['path'], headers, msgdata))
            elif path.strip('/') == command[1]:
                if method.upper() == 'POST':
                    self.send(parse_header(headers, 405) + b'\r\n')
                    continue
                self.send(process_delete(parameters['path'], headers))
            else:
                if method.upper() == 'POST':
                    self.send(parse_header(headers, 405) + b'\r\n')
                    continue
                sustech = 'SUSTech-HTTP' in parameters and parameters['SUSTech-HTTP'] == '1'
                if 'chunked' in parameters:
                    headers['Chunked'] = parameters['chunked']
                head = method.upper() == 'HEAD'
                process_download(con, path.strip('/'), headers, sustech, head, self.cipher)
            
            if headers['Connection'].lower() == 'close':
                con.close()
                return

    def send(self, data):
        if encrypt:
            self.request.sendall(self.cipher.encrypt(pad(data, 16, style='pkcs7')))
        else:
            self.request.sendall(data)

if __name__ == "__main__":
    server = ThreadingServer((IP, PORT), RequestHandler)
    Thread(target=server.serve_forever).start()
