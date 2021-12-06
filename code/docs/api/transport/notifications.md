# Cities API
[Notifications List API](#notifications-list)       
[Create Notification API](#create-notification)    
[Single Notification API](#single-notification)    
[Resolving Notification API (aka deleting)](#resolve-notification)    




### Notifications List   
***/transport/organization/v1/notifications***  
access roles - \>=transport_admin     
```javascript
// get notifications list
request (GET):
    params: 
        resolved: bool = false
    
response:
    {
      "notifications": [ Notification* ], 
      "message": "OK", 
      "status": 200
    }
```



### Create Notification   
***/transport/organization/v1/notifications***  
access roles - \>=transport_admin    
```javascript
request (POST):
    params:
        type: str                       // 'error', 'warning', 'test', ...
        domain: str                     // 'transport', 'engine'
        title: str                      // 'Speed violation'
        сontent: str                    // 'Some transport reached max speed at 12:00pm'
        resolved: bool = false
        attributes: dict = null         // {"speed": 78.5, "date": "2018-05-10 12:00"}
        payload: dict = null            // any dict

response:
    {
        "message": "OK",
        "notification": Notification*,
        "status": 200
    }
```
 - See [Notification Type](#notification-type)





### Single Notification   
***/transport/organization/v1/notifications/\<int:notification_id\>***  
access roles - \>=transport_admin    
```javascript
request (GET):
    params:
        notification_id: int 

response:
    {
        "message": "OK",
        "notification": Notification*,
        "status": 200
    }
```
 - See [Notification Type](#notification-type)




### Resolve Notification   
***/transport/organization/v1/notifications/\<int:notification_id\>***  
access roles - \>=transport_admin    
```javascript
request (PATCH):
    params:
        notification_id: int 

response:
    {
        "message": "OK",
        "notification": Notification*,
        "status": 200
    }
```
 - See [Notification Type](#notification-type)



#### Notification Type
```javascript
{
    "attributes": {                 // any json
        "passengers_in": 100,
        "speed": 78.5
    },
    "content": "Speeed aaaa",       // text of notification
    "domain": "transport",
    "id": 5,
    "organization": 2,
    "payload": null,                // any json
    "resolved": false,
    "title": "Speed violation", 
    "type": "warning"
}
```
