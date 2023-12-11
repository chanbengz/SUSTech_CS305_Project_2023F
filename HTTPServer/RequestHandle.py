import datetime, base64, uuid, time
import sqlite3 as sql
import os, pathlib, shutil, mimetypes

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
    if 'Content-Length' in headers:
        res_header += 'Content-Length: ' + str(headers['Content-Length']) + '\r\n'
    if 'Connection' in headers:
        if headers['Connection'].lower() == 'keep-alive':
            res_header += 'Keep-Alive: timeout=' + str(timeout) + ', max=' + str(maxconnect) + '\r\n'
            res_header += 'Connection: keep-alive\r\n'
        elif headers['Connection'].lower() == 'close':
            res_header += 'Connection: close\r\n'
    if 'Set-Cookie' in headers:
        res_header += 'Set-Cookie: ' + headers['Set-Cookie'] + '\r\n'
    if 'Chunked' in headers and headers['Chunked'] == '1':
        res_header += 'Transfer-Encoding: chunked\r\n'    
    if 'WWW-Authenticate' in headers:
        res_header += 'WWW-Authenticate: ' + headers['WWW-Authenticate'] + '\r\n'
    if 'Content-Type' in headers:
        res_header += 'Content-Type: ' + headers['Content-Type'] + '\r\n'
    if 'Content-Range' in headers:
        res_header += 'Content-Range: ' + headers['Content-Range'] + '\r\n'
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
    current_user = path.split('/')[0]
    headers['Content-Length'] = 0
    if headers['User'] != current_user:
        return parse_header(headers, 401) + b'\r\n'
    path = 'data/' + path
    if os.path.exists(path):
        if os.path.isfile(path):
            os.remove(path) 
            print('Delete file: ' + path)
            response = parse_header(headers, 200) + b'\r\n'
        elif os.path.isdir(path):
            shutil.rmtree(path)
            print('Delete directory: ' + path)
            response = parse_header(headers, 200) + b'\r\n'
    else:
        response = parse_header(headers, 404) + b'\r\n'
    return response + b'\r\n'

def process_upload(path, headers, msgdata):
    path = path.strip('/')
    current_user = path.split('/')[0]
    if headers['User'] != current_user:
        return parse_header(headers, 401) + b'\r\n'
    headers['Content-Length'] = 0
    boundary = '--' + headers['Content-Type'].split('=')[1]
    path = 'data/' + path
    files = msgdata.split(boundary)[1:-1]
    for file_data in files:
        file_data = file_data.strip('\r\n')
        name, content = parse_formdata(file_data)
        file_path = os.path.join(path, name)
        with open(file_path, 'wb') as file:
            file.write(content.encode())
        print('Created file:', file_path)
    response = parse_header(headers, 200) + b'\r\n'
    return response + b'\r\n'

def process_download(con, path, headers, sustech, head):
    headers['Content-Length'] = 0
    path = 'data/' + path
    Path = pathlib.Path(path)
    if Path.is_dir():
        if sustech:
            file_names = [entry.name + '/' if entry.is_dir() else entry.name for entry in Path.iterdir()]
            msgdata = file_names.__str__().encode()
            headers['Content-Type'] = 'text/plain'
        else:
            msgdata = render_homepage(path)
            headers['Content-Type'] = 'text/html'
        headers['Content-Length'] = len(msgdata)
        response = parse_header(headers, 200) + b'\r\n' + msgdata + b'\r\n'
        con.sendall(response)
        return
    else:
        if os.path.exists(path):
            if headers.get('Chunked') == '1':
                response = parse_header(headers, 200) + b'\r\n'
                with open(path, 'rb') as file:
                    headers['Content-Type'] = mimetypes.guess_type(path)[0]
                    while True:
                        con.sendall(response)
                        data = file.read(1024)
                        if not data:
                            break
                        response = hex(len(data)).encode() + b'\r\n' + data + b'\r\n'
                con.sendall(b'0\r\n\r\n')
                return
            elif 'Range' in headers:
                range = parse_range(headers['Range'], os.path.getsize(path))
                if range is None:
                    response = parse_header(headers, 416) + b'\r\n'
                    con.sendall(response)
                    return
                if len(range) > 1:
                    boundary = str(uuid.uuid4())
                    headers['Content-Type'] = 'multipart/byteranges; boundary=' + boundary
                    response_body = generate_multipart_response(file_path, ranges, boundary)
                    response = parse_header(headers, 206) + b'\r\n' + response_body + b'\r\n'
                else:
                    start, end = range[0]
                    print(start, end)
                    headers['Content-Type'] = mimetypes.guess_type(path)[0]
                    headers['Content-Range'] = 'bytes {start}-{end}/{total}'.format(start=start, end=end, total=os.path.getsize(path))
                    response_body = read_partial_file(path, start, end)
                    print(response_body)
                    headers['Content-Length'] = len(response_body)
                    response = parse_header(headers, 206) + b'\r\n' + response_body + b'\r\n'
            else:
                with open(path, 'rb') as file:
                    file_content = file.read()
                    headers['Content-Type'] = mimetypes.guess_type(path)[0]
                headers['Content-Length'] = file_content.__len__()
                response = parse_header(headers, 200) + b'\r\n' + file_content if not head else b'' + b'\r\n'
        else:
            response = parse_header(headers, 404) + b'\r\n'
    con.sendall(response)

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
    except:
        headers['User'] = None
        headers['WWW-Authenticate'] = 'Basic realm="Authorization Required"'
    finally:
        user_database.close()
        cookie_database.close()
    
    return headers

def parse_formdata(data):
    tmp = data.split('\n')
    name = ''
    content = ''
    for i in tmp[0].split('; '):
        if i.startswith('name'):
            name = i.split('=')[1].strip('"')
    for i in range(2, len(tmp)):
        content += tmp[i] + '\n'
    return name, content

def render_homepage(path):
    current = pathlib.Path(path)
    page = home_page.decode()
    page = page.replace('{{path}}', path.strip('data/'))
    page = page.replace('{{root}}', '/' + path.split('/')[1])
    item_str = ''
    for entry in current.iterdir():
        name = entry.name
        if name.startswith('.'):
            continue
        path = entry.__str__()[5:]
        isdir = entry.is_dir().__str__().lower()
        item_str += "{ " + f"name: '{name}', path: '{path}', isDirectory: {isdir}" + " },\n"
    page = page.replace('{{items}}', item_str)
    return page.encode()

def parse_range(range_header, entity_length):
    if not range_header.startswith('bytes='):
        return None
    
    range_header = range_header[6:]
    ranges = range_header.split(',')
    result = []
    for r in ranges:
        if '-' in r:
            start, end = r.split('-')
            if start == '':
                # 结尾范围，如 "bytes=-500"
                start = entity_length - int(end)
                end = entity_length - 1
            elif end == '':
                # 起始范围，如 "bytes=9500-"
                start = int(start)
                end = entity_length - 1
            else:
                # 起始和结束范围，如 "bytes=500-999"
                start = int(start)
                end = int(end)
            if start <= end and end < entity_length:
                result.append((start, end))
            else:
                return None

    return result

def read_partial_file(file_path, start, end):
    print(file_path, start, end)
    with open(file_path, 'rb') as file:
        file.seek(start)
        content = file.read(end - start + 1)
    return content
        

def generate_multipart_response(file_path, ranges, boundary):
    response_parts = []
    for start, end in ranges:
        content_range = 'bytes {start}-{end}/{total}'.format(start=start, end=end, total=os.path.getsize(file_path))
        partial_content = read_partial_file(file_path, start, end)
        mime_type, _ = mimetypes.guess_type(file_path)
        part = []
        part.append('--' + boundary)
        part.append('Content-Type: ' + mime_type)
        part.append('Content-Range: ' + content_range)
        part.append('')
        part.append(partial_content)
        response_parts.append('\r\n'.join(part))

    response = []
    response.append('\r\n'.join(response_parts))
    response.append('--' + boundary + '--')

    return '\r\n'.join(response).encode()