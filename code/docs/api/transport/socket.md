# Connection to SocketIO
### namespace:    
(New) Public with shuttle buses = '/transport/v2'   
public transport namespace = '/transport'   
admin transport namespace = '/transport/admin'    
driver transport namespace = '/transport/driver'   
(deprecated) public namespace = '/'   

### Headers:

```
{"Authorization": "Bearer TOKEN"}
```


## /transport || /transport/v2
access level - public
#### Events
   * ["subscribe" - receive data](subscribe.md#public-subscribe)
   * "join" - join the room
   * "leave" - leave the room
   * ["status"](#status-event) - connection alive status (must return any data to show liveness, otherwise you will be disconnected)

#### Rooms:
   * "city_<id>" - all active transport in given city
   * line_id - all active transport by line

## /transport/admin
#### Events
   * ["subscribe" - receive data](subscribe.md#admin-subscribe-structure)
   * "join" - join the room
   * "leave" - leave the room
   * "status" - connection alive status (must return any data to show liveness, otherwise you will be disconnected)
   * ["notification" - receive notification](/docs/api/transport/notifications.md#notification-type)
#### Rooms:
   * "all" - all active transport in your organization
   * line_id - all active transport by line
 
## /transport/driver
You automatically connected to your transport's line room
#### Events
   * ["subscribe" - receive data](subscribe.md#admin-subscribe-structure)
   * "status" - connection alive status (must return any data to show liveness, otherwise you will be disconnected)

# Examples:
### Connect
```
SocketIO(host="host",
         port="port",
         headers={"Authorization": "Bearer TOKEN"})
```

### Join room
```
SocketIO.emit("join", 1420)
```
### Join to several rooms
```
SocketIO.emit("join", 12, 66)

OR
send rooms name as array
SocketIO.emit("join", [12, 66])
```

### Leave room
```
SocketIO.emit("leave", 1420)
```
### Leave several rooms
```
SocketIO.emit("leave", 12, 66)
or
send rooms name as array
SocketIO.emit("leave", [12, 66])
```
### [Receive data](subscribe.md)
```
SocketIO.on("subscribe", handle_function(data))
```
### Status event
```javascript
socketio.on('status', function(data){socketio.emit('status', data)})
```
