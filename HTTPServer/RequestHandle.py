import datetime
from HTTPServer.FileOperation import *

home_page = open('public/index.html', 'rb').read()
icon = open('public/favicon.ico', 'rb').read()
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
maxconnect = 100
timeout = 120
command = [
    'upload',
    'delete'
]

def parse_header(headers, code):
    res_header = ''
    res_header += http_version + ' ' + str(code) + ' ' + status_code[code] + '\r\n'
    res_header += 'Server: ' + 'Python HTTP Server' + '\r\n'
    res_header += 'Date: ' + datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT') + '\r\n'
    if 'Connection' in headers:
        if headers['Connection'].lower() == 'keep-alive':
            res_header += 'Keep-Alive: timeout=' + str(timeout) + ', max=' + str(maxconnect) + '\r\n'
            res_header += 'Connection: keep-alive\r\n'
        elif headers['Connection'].lower() == 'close':
            res_header += 'Connection: close\r\n'
    if 'Set-Cookie' in headers:
        res_header += 'Set-Cookie: ' + headers['Set-Cookie'] + '\r\n'
    return res_header.encode('utf-8')

def parse_request(request):
    request = request.split('\r\n')
    method, path, protocol = request[0].split(' ')
    data = request[-1]
    result = dict()
    for i in range(1, len(request) - 1):
        if request[i] == '':
            continue
        key, value = request[i].split(': ')
        result[key.title()] = value
    return method, path, protocol, result, data

def process_get(path, headers):
    if path == '/favicon.ico':
        data = icon
    else:
        data = home_page
    return process_head(path, headers) + data


def process_post(path, headers, msgdata):
    pass

def process_head(path, headers):
    res_header = parse_header(headers, 200)
    if path == '/favicon.ico':
        data = icon
        res_header += b'Content-Type: image/x-icon\r\n'
    else:
        data = home_page
        res_header += b'Content-Type: text/html\r\n'
    res_header += b'Content-Length: ' + bytes(len(data)) + b'\r\n'
    return res_header + b'\r\n'