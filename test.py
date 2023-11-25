import requests

headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
session = requests.Session()
session.headers.update({'Connection': 'keep-alive'})

response = session.get('http://127.0.0.1:8080',headers=headers)

print(response)