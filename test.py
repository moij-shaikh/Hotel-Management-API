import json 

my={
    1:12,
    12:450,
    "helo":4
}
data=json.dumps(my)
print(my)
print(data)

new=json.loads(data)