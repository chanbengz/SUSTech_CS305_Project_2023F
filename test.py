import requests, time

# headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
headers = {'Cookie': 'session-id=491dbe9e024940c08dfe8220b2367d2d'}
session = requests.Session()
session.headers.update({'Connection': 'keep-alive'})

response = session.head('http://127.0.0.1:8080',headers=headers)
print(response)
print(response.cookies)
session.close()