import requests, time

# headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
headers = {'Cookie': 'session-id=1ec73008cfd84f3a9aeb138a094fe807'}
session = requests.Session()
session.headers.update({'Connection': 'keep-alive'})

response = session.head('http://127.0.0.1:8080',headers=headers)
print(response)
print(response.cookies)
session.close()