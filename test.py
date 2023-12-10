import requests

headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
# headers = {'Cookie': 'session-id='}
session = requests.Session()
session.headers.update({'Connection': 'keep-alive'})
files = {'a.txt': open('data/a.txt', 'rb'),'a.py': open('data/a.py', 'rb')}
#response = session.post(url='http://127.0.0.1:8080/upload?path=client1/', headers=headers, files=files)
response = session.get('http://localhost:8080/delete?path=client2/test', headers=headers)
#response = session.get('http://localhost:8080/client1/a.txt', headers=headers)
print(response)
print(response.headers)
print(response.cookies)
print(response.content)
# response = session.head('http://127.0.0.1:8080/?SUSTech-HTTP=1&path=', headers=headers)
# print(response)
# print(response.cookies)
# session.close()