import requests

url = 'http://192.168.1.6:8081/paraview'
myobj = {'application': 'trame', 'useUrl': True}

x = requests.post(url, json = myobj)

print(x.text)