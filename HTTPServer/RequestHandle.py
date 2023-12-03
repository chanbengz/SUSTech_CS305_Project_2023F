import datetime, base64, uuid, time
import sqlite3 as sql

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
command = ['upload', 'delete']

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
    if 'WWW-Authenticate' in headers:
        res_header += 'WWW-Authenticate: ' + headers['WWW-Authenticate'] + '\r\n'
    return res_header.encode('utf-8')

def parse_request(request):
    request = request.split('\r\n')
    method, path, protocol = request[0].split(' ')
    data = ''
    result = dict()
    end_of_header = 0
    for i in range(1, len(request)):
        if request[i] == '':
            end_of_header = i
            break
        key, value = request[i].split(': ')
        result[key.title()] = value
    for i in range(end_of_header + 1, len(request)):
        data += request[i] + '\n'
    return method, path, protocol, result, data

def process_delete(path, headers):
    pass

def process_upload(path, headers, msgdata):
    pass

def process_download(path, headers):
    pass

def process_head(path, headers):
    datalen = 0
    res_header = parse_header(headers, 200) if 'WWW-Authenticate' not in headers else parse_header(headers, 401)
    res_header += b'Content-Type: text/html\r\n'
    res_header += b'Content-Length: ' + str(datalen).encode() + b'\r\n'
    return res_header + b'\r\n'

def process_icon(headers):
    res_header = parse_header(headers, 200)
    res_header += b'Content-Type: image/x-icon\r\n'
    res_header += b'Content-Length: ' + str(len(icon)).encode() + b'\r\n'
    return res_header + b'\r\n' + icon

def parse_path(path):
    if '?' not in path:
        return path, dict()
    path, tmp = path.split('?')
    parameters = dict()
    for parameter in tmp.split('&'):
        key, value = parameter.split('=')
        parameters[key] = value
    return path, parameters

def authenticate(headers):
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
                    headers['User'] = username
                else:
                    raise
            else:
                raise
        else:
            duration = 3600
            session_id = headers['Cookie'].split('=')[1]
            for result in cookie_database.execute(f"select * from cookies where session_id = '{session_id}';"):
                headers['User'] = result[0]
                duration = int(time.time()) - result[2]
            if duration >= 3600:
                cookie_database.execute(f"delete from cookies where session_id = '{session_id}';")
                raise
    except:
        headers['User'] = None
        headers['WWW-Authenticate'] = 'Basic realm="Authorization Required"'
    finally:
        user_database.close()
        cookie_database.close()
    
    return headers