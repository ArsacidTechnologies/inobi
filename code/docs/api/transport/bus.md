[Ping From Bus](#ping-from-bus)  
[List Of Buses](#list-of-buses)  
[Create New Bus](#create-new-bus)  
[Update Existing Bus](#update-existing-bus)  
[Delete Bus](#delete-bus)  
[List Of Unknown Buses](#list-of-unknown-buses)  


### Ping from bus
***/transport/bus***   
access roles - transport_device, transport_admin   
pass JWT in [params](#hybrid-parameters)
```javascript
request:
    POST
        id: str (Required),
        lat: float (Required),
        lng: float (Required)
response:
    "message": str,
    "status": int
```
### LIST OF BUSES  
***/transport/organization/v1/buses***   
access roles - transport_admin, transport_viewer   
pass JWT in [params](#hybrid-parameters)
```javascript
request:
    GET
        no params
response:
    data:[
        Transport (*),
    ],
    message: str,
    status: int
    
```
### LIST OF BUSES INFO  
***/transport/v1/buses/info***   
access roles - transport_admin
pass JWT in [params](#hybrid-parameters)
```javascript
request:
    GET
        no params
response:
    data:[
        BusInfo (*),
    ],
    message: str,
    status: int
    
```
### STATUS REPORT
***/transport/organization/v1/reports/status***   
access roles - transport_viewer
pass JWT in [params](#hybrid-parameters)
```javascript
request:
    GET
        id: int (Required),
        from_time: string, UTC datetime `%Y-%m-%d %H:%M:%S` (Required),
        to_time: string, UTC datetime `%Y-%m-%d %H:%M:%S` (Required)
response:
    data:[
            {
                device_id: int,
                total_time_on: int,
                total_time_off: int
            },
         ],
    message: str,
    status: int

```
### ANIMATION REPORT
***/transport/organization/v1/reports/animation***   
access roles - transport_viewer
pass JWT in [params](#hybrid-parameters)
```javascript
request:
    GET
        id: int (Required),
        from_time: string, UTC datetime `%Y-%m-%d %H:%M:%S` (Required),
        to_time: string, UTC datetime `%Y-%m-%d %H:%M:%S` (Required)
response:
    data:[
            Positions(*)
         ],
    message: str,
    status: int

```
[Transport](#transport-structure) 
### CREATE NEW BUS  
***/transport/organization/v1/buses***   
access roles - transport_admin   
pass JWT in [params](#hybrid-parameters)
```javascript
request:
    POST application/json
        params:
            device_id: str (Required),
            line_id: int (Required),
            device_phone: str (Optional),
            independent: boolean (Optional),
            line_id: int (Optional),
            name: str (Optional),
            payload: dict (Optional),
            ip: str (Required),
            port: int (Required),
            tts: int (Required),
        
response:
    data: Transport (*)
    message: str,
    status: int
```
[Transport](#transport-structure) 
### UPDATE EXISTING BUS  
***/transport/organization/v1/buses***   
access roles - transport_admin   
pass JWT in [params](#hybrid-parameters)
```javascript
request:
    PATCH - update only given params
        id: int (Required),
        device_id: str (Optional),
        line_id: int (Optional),
        device_phone: str (Optional),
        independent: boolean (Optional),
        line_id: int (Optional),
        name: str (Optional),
        payload: dict (Optional),
        ip: str (Required),
        port: int (Required),
        tts: int (Required),
        
    PUT - replace transport
        id: int (Required),
        device_id: str (Required),
        line_id: int (Required),
        device_phone: str (Required),
        independent: boolean (Required),
        line_id: int (Required),
        name: str (Required),
        payload: dict (Optional),
        ip: str (Required),
        port: int (Required),
        tts: int (Required),
        
        
response:
    data: Transport (*)
    message: str,
    status: int
```
[Transport](#transport-structure) 
### DELETE BUS  
***/transport/organization/v1/buses***   
access roles - transport_admin   
pass JWT in [params](#hybrid-parameters)
``` javascript
request:
    DELETE
       id: int (Required)
response:
    data: Transport (*)
    message: str,
    status: int
```
[Transport](#transport-structure) 
### LIST OF UNKNOWN BUSES  
***/transport/v2/unknowns***   
access roles - transport_inobi   
pass JWT in [params](#hybrid-parameters)
```javascript
request:
    GET
        no params
response:
    data:[
        Transport (*),
    ],
    message: str,
    status: int
```    
[Transport](#transport-structure) 
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


### Transport Structure
```javascript
{
    "id": int,
    "device_id": str,
    "device_phone": str (null),
    "driver": int (null),
    "independent": bool,
    "line_id": int,
    "name": str (null),
    "payload": dict (null)
}
```   
