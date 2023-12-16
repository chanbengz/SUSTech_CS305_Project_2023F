import requests

headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
# headers = {'Cookie': 'session-id=e080da43-6892-4751-bce9-bad73d3e875b'}

session1 = requests.Session()
session1.headers.update({'Connection': 'keep-alive'})
session2 = requests.Session()
session2.headers.update({'Connection': 'keep-alive'})

# Test persistent connection
# session.headers.update({'Connection': 'close'})

# Test chunked
# session.headers.update({'Range': 'bytes=0-1,1-2,2-3'})

# Test upload
# files = {'a.zip': open('Test/a.zip', 'rb'),'a.py': open('data/a.py', 'rb')}
# response = session.post(url='http://127.0.0.1:8080/upload?path=/client1/', headers=headers, files=files)

# response = session.get('http://localhost:8080/client1/a.txt?chunked=1', headers=headers)

# Test download
response = session1.get('http://localhost:8080/client1/a.py', headers=headers)

print(response)
print("--------------------\n")
for key, value in response.headers.items():
    print(key + ': ' + value)
print(response.cookies.values()[0])
print()
print(response.content)

# Test download
response = session2.get('http://localhost:8080/client2/a.py', headers=headers)

print(response)
print("--------------------\n")
for key, value in response.headers.items():
    print(key + ': ' + value)
print(response.cookies.values()[0])
print()
print(response.content)
