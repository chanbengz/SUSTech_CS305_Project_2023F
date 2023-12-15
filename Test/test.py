import requests

headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
# headers = {'Cookie': 'session-id=e080da43-6892-4751-bce9-bad73d3e875b'}

session = requests.Session()
session.headers.update({'Connection': 'keep-alive'})

# Test persistent connection
# session.headers.update({'Connection': 'close'})

# Test chunked
# session.headers.update({'Range': 'bytes=0-1,1-2,2-3'})

# Test upload
# files = {'a.txt': open('data/a.txt', 'rb'),'a.py': open('data/a.py', 'rb')}
# response = session.post(url='http://127.0.0.1:8080/upload?path=client1/', headers=headers, files=files)

# Test download
# response = session.get('http://localhost:8080/delete?path=client2/test', headers=headers)

response = session.get('http://localhost:8080/client1/a.txt?chunked=1', headers=headers)

print(response)
print("--------------------\n")
print(response.headers)
print("\n--------------------\n")
print(response.cookies.values()[0])
print(response.content)

# response = session.post(url='http://127.0.0.1:8080/upload?path=client1/', headers=headers, files=files)