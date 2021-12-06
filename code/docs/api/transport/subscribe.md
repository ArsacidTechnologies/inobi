### admin subscribe
***/transport/organization/v1/subscribe***   
access roles - transport_admin, transport_inobi   
pass JWT in [params](#hybrid-parameters)
```javascript
request
    POST
        line_id: 
            ONE OF BELOW
            str("all") - to all lines
            int - to specific line
            array of int - to array of lines
        type: 
            ONE OF BELOW
            str ("public") - public type data
            str ("admin") - admin type data
        inactive: 
            bool (true, false)
response
    "data": [
        Admin Subscibe (*)
    ],
    "message": str,
    "status": int
```
[Admin Subscibe](#admin-subscribe-structure)   
### subscribe
access roles - all  
pass JWT in [params](#hybrid-parameters)   
***/transport/v2/subscribe***   
***/transport/v3/subscribe***(New) with shuttle buses
```javascript
request
    POST, GET
        line_id: // pass in params(*) 
            ONE OF BELOW
            str("all") - to all lines
            int - to specific line
            array of int - to array of lines
response
    {
        "data": [
            Public Subscribe (*)
        ],
        "message": "OK",
        "status": 200
    }
```   
[params](#hybrid-parameters)   
[Public Subscribe](#public-subscribe-structure)

### driver subscribe
access roles - transport_admin transport_driver  
pass JWT in [params](#hybrid-parameters)
***/transport/v2/driver/subscribe***
```javascript
request
    POST, GET:
        without params
response
    {
        "data": [
            Admin Subscribe (*)
        ],
        "message": "OK",
        "status": 200
    }
``` 
[Public Subscribe](#admin-subscribe-structure)

#### Public Subscribe Structure
```javascript
{
    "bearing": flaot,
    "id": int,
    "line_id": int,
    "location": {
        "lat": flaot,
        "lng": float
    },
    "name": str,
    "path": [
        {
            "lat": float,
            "lng": float,
            "time": float
        },
        ...
        ,
    ],
    "time": float
}
```
#### Admin Subscribe Structure
```javascript
{
    "bearing": float,
    "device_id": str,
    "device_phone": str,
    "driver": int (null),
    "id": int,
    "independent": bool,
    "line_id": int,
    "location": {
        "lat": float,
        "lng": float
    },
    "name": str,
    "path": [
        {
            "lat": float,
            "lng": float,
            "time": float
        },
        ...
        ,
    ],
    "payload": dict (null),
    "time": float
},
```


### Hybrid Parameters
Hybrid parameters are parameters that can be sent as GET arguments
or as root attributes in JSON in POST-request's body   
Example:

**?some=value&another=maybe**

*as same as*

**{
  "some": value,
  "another": "maybe"
}**

***Note*** that some arguments in endpoints are required to be complex objects
and can not be described as GET argument. In those cases POST request must be
performed (since somehow those object must be sent) todo: objects as get-args
