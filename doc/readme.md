# Cloud Platform
## web to host
```
{
    "header": "web",
    "request":{
        "type":[ "account" | "instance" ],
        "request": request_body,
    }
}
```
### request_body for account:
```
create user:
{
    "method": "create",
    "user_name": "your_name",
    "passwd": "passwd",
}

change passwd:
{
    "method": "alter"
    "user_name": "your_name",
    "passwd": "newpasswd,
}
```
### request_body for instance:
```
{
    "user_name": "your_name",
    "request": request_body
}
#For more information of request_body. Please read host to meta 
```

## host to meta:
```
{
    "method": ["CVM" | "CVN" | "DVM"]
    "request": request_body
}
```
### create vm:
```
{
    "user_name": user_name,
    "passwd": passwd,
    "instance_id": instance_id,
    "memory": ram,
    "disk_size": disk_size,
    "vcpu": vcpu,
    "OSType": os_type
}
```
### destroy vm:
```
{
    "user_name": user_name,
    "instance_id": instance_id
}
```
### create vnet:
```
{'name': request.get('user_name'),
    'type': 'vnet',
    'gateway': request.get('gateway'),
    'seq': 1
}
```
