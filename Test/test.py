import requests

url='http://127.0.0.1:8080/delete?p=abc'

data={}
headers={"Authorization": "Basic Y2xpZW50MToxMjM="}
r=requests.get(url=url, data=data, headers=headers)
print(r.status_code)
