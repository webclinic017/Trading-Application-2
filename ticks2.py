import json


f = open("2020-09-03.txt", "r")
for x in f:
    print(x)
    response = json.dumps(x)
    refined = json.loads(response)
    print(refined)

