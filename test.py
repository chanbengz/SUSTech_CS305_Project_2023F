import requests, time

headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
# headers = {'Cookie': 'session-id='}
session = requests.Session()
session.headers.update({'Connection': 'keep-alive'})
files = {'a.txt': open('data/client1/a.txt', 'rb'), 'a.py': open('data/client1/a.py', 'rb')}
r=requests.post(url='http://127.0.0.1:8080/upload?path=client1/', headers=headers, files=files)
print(r)
response = session.get('http://127.0.0.1:8080/', headers=headers)
print(response)
print(response.headers)
print(response.cookies)
# response = session.head('http://127.0.0.1:8080/?SUSTech-HTTP=1&path=', headers=headers)
# print(response)
# print(response.cookies)
# session.close()