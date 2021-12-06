# Driver API

[Points Of Awareness](#points-of-awareness)   
[Driver Transport Manipulation](#driver-transport-manipulation)      
[Subscribe](#subscribe)   


### Subscribe
#### HTTP
***/transport/v2/driver/subscribe***   
access roles - transport_driver   
```javascript
request:
    GET:
        params:
            None
        response:
            {
                "data": [Subscribe (*)], // list of Subcribe
                "message": "OK",
                "status": 200
            }
```   
[Subscribe structure](/docs/api/transport/subscribe.md#admin-subscribe-structure)
#### WEB SOCKET   
***/transport/driver***   
access roles - transport_driver   
[driver web socket](/docs/api/transport/socket.md)   

### Points Of Awareness
***/transport/driver/v1/points***    
access roles - application_public <br />
--[hybrid params](#hybrid-parameters)-- <br />
```javascript
request:
    GET:
        params:
            None
            
        response:
            {
                "points": [Point (*)],      // list of Points
                "count": 0,                 // count of points list
                "message": "OK",
                "status": 200
            }
    
    POST:
        params:
            lat: float,
            lng: float,
            description: str = None,
            payload: dict = None
            exp: float = 300                // expiration of point (in seconds)
        
        response: 
            {
                "accepted_point": Point (*),
                "message": "OK",
                "status": 200
            }
    
    DELETE: 
        params: 
            id: uuid(str)
            
        response:
            {
                "deleted_point": Point (*),
                "message": "OK",
                "status": 200
            }
```
- [Point](#point-type)   

### Driver Transport Manipulation   
***/transport/driver/v1/transports***    
access roles - transport_driver    
--[hybrid params](#hybrid-parameters)-- <br />
```javascript
request:
    GET: // available transports
        params:
            None
        response:
            {
                "transports": [Transport (*)],      // list of Transports
                "message": "OK",
                "status": 200
            }
    
    POST: // check in transport
        params:
            transport: int,     // id of transport
        response: 
            {
                "transport": Transport (*),
                "message": "OK",
                "status": 200
            }
    
    DELETE: // check out transport
        params:
            None
        response: 
            {
                "transport": Transport (*),
                "message": "OK",
                "status": 200
            }
```   
- [Transport](/docs/api/transport/bus.md#transport-structure)   

### Point Type
```javascript
{
    "id": "84b748fb-9e24-4d7f-a633-faa87f8aa7d7",
    "info": {
        "description": "Police!!",
        "lat": 2.0,
        "lng": 8.0,
        "payload": null,
        "type": "be_aware"
    },
    "time": 1519797389.611069,
    "exp": 1519797689.611069
    "iss": 7,
    "driver": {
        "id": 7,
        "transport": 1
    }
    "updates": [],
}
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

