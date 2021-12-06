[Get Line Info](#get-line-info)  
[List Of Lines](#list-of-lines)  
[List Of Platforms By View Port](#list-of-platforms-by-view-port)  
[List Of Routes By Platform Id](#list-of-routes-by-platform-id)

### GET LINE INFO
***/transport/organization/v1/lines/{id}***  
access roles - transport_admin   
pass JWT in [params](#hybrid-parameters)
```
request:
    GET
        id: int (Required)
response:
        "data": 
                "directions": array of Direction*
                Line*
        "message": str,
        "status": int
```
[Direction](#direction-structure)   
[Line](#line-structure)
### List of lines
***/transport/organization/v1/lines***   
access roles - transport_admin   
pass JWT in [params](#hybrid-parameters)
```
request:
    GET no params
response:
        "data": Line*
        "message": str,
        "status": int
```
[Line](#line-structure)
### List of platforms by view port
***/transport/platforms***
```
request
    POST
        Headers:
            {"Authorization": "Bearer {TOKEN}"}
            {"Content-Type": "application/json"}
        Body:
            {
                [dictionary] top right point
                "start_point":{
                    "lat":42.877552,
                    "lng":74.693438
                },
                [dictionary] buttom left point
                "end_point":{
                    "lat":42.876106,
                    "lng":74.69612
                }
            }
response
    {
        [dictionary] array of platforms in view port
        "data": [
            {
                "full_name": "Бишкек, Городок Энергетиков (ул. Энергетиков городок)",
                "id": 898,
                "location": {
                    "lat": 42.87693405151367,
                    "lng": 74.69416046142578
                },
                "name": "Городок Энергетиков (ул. Энергетиков городок)"
            },
            {
                "full_name": "Бишкек, Городок Энергетиков (ул. Энергетиков городок)",
                "id": 900,
                "location": {
                    "lat": 42.876922607421875,
                    "lng": 74.69401550292969
                },
                "name": "Городок Энергетиков (ул. Энергетиков городок)"
            }
        ],
        "message": "OK",
        "status": 200
    }
```
### List of routes by platform id
***/transport/platform_routes***
```
request
    POST
        Headers:
            {"Authorization": "Bearer {TOKEN}"}
            {"Content-Type": "application/json"}
        Body:
            {
                "id":900
            }
    GET
        Headers:
            {"Authorization": "Bearer {TOKEN}"}
        Params:
            id = 900
response
    {
        "data": {
            "bus": [...],
            "shuttle_bus": [
                {
                    "from_name": "Парк Победы",
                    "id": 895,
                    "name": "152",
                    "to_name": "Городок Энергетиков (ул. Энергетиков городок)",
                    "type": "shuttle_bus"
                }
            ],
            "trolleybus": [...]
        },
        "message": "OK",
        "status": 200
    }
```


### Line Structure   
```javascript
{
    "id": int,
    "name": str,
    "from_name": str,
    "to_name": str,
    "type": str
}
```   

### Platform Structure
```javascript
{
    "id": int,
    "name": str,
    "full_name": str,
    "location": dict ("lat": float,
                      "lng": float)
}
```  

### Direction Structure
```javascript
{
    "id": int,
    "line": str (polylne format*),
    "type": str,
    "platforms": array of Platforms*
}
``` 
polyline https://developers.google.com/maps/documentation/utilities/polylineutility
[Platform](#platform-structure)



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

