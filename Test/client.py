import socket, requests
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes

data = b'''GET /client1/a.txt HTTP/1.1
Host: localhost:8080
User-Agent: python-requests/2.28.2
Accept-Encoding: gzip, deflate
Accept: */*
Connection: close
Authorization: Basic Y2xpZW50MToxMjM=\r\n\r\n'''

con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
con.connect(('', 8080))
client_key = get_random_bytes(16)
iv = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F'
cipher = AES.new(client_key, AES.MODE_CBC, iv)
decryptor = AES.new(client_key, AES.MODE_CBC, iv)
server_public_key = con.recv(4096)
server_key = RSA.import_key(server_public_key)
encryptor = PKCS1_OAEP.new(server_key)
con.sendall(encryptor.encrypt(client_key))

con.sendall(cipher.encrypt(pad(data.replace(b'\n', b'\r\n'), 16, style='pkcs7')))
print(unpad(decryptor.decrypt(con.recv(2048)), 16, style='pkcs7').decode())
