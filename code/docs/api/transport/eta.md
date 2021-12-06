# ETA API


### Platform's eta
#### HTTP
***/transport/eta/v1/platforms***   
access roles - public 
```javascript
request:
    POST:
        params:
            id: int // platform id
            routes: [int] //Optional - array of route ids
        response:
            {
                "transports": [ETA (*)], // eta
                "message": "OK",
                "status": 200,
                "time": int // timestamp - server time
            }
```   
### Transport's eta
#### HTTP
***/transport/eta/v1/transports***   
access roles - public 
```javascript
request:
    POST:
        params:
            id: int // transport id
        response:
            {
                "platforms": [ETA (*)], // eta
                "message": "OK",
                "status": 200,
                "time": int // timestamp - server time
            }
```   
  

### ETA 
```javascript
{
    "transport_id": int,
    "platform_id": int,
    "line_id": int,         
    "eta_time": int         // seconds
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

