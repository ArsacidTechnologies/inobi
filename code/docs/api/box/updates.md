
# Updates API

Boxes get updates through this API.
Firstly every box stores its version (usually at its filesystem's /version file).
Then it loops with an interval (usually 15 mins) checks server's last version through [Version API](#box-version).
If it sees version other than its current, it fetches update script using [Update API](#box-update), then executes its content.

Admins can upload [new update script](#admin-box-update), [upload external files](#admin-upload-external) and [change current server's version](#admin-box-version).
To make this requests it needs to [login](#admin-login) first to get `API_TOKEN` and use it in above APIs like `Authorization: Bearer $TOKEN` header or `?token=$TOKEN` GET-argument to get access.

Current it is necessary to deliver some files on boxes' filesystem, that's why [Upload External Files API](#admin-upload-external) exists.
It can be used to upload any file to server, then fetch it when needed.
Currently its used like this: 
all update files bundled in *.tar.gz file, then uploaded to this API. 
In update script then used `wget` or `curl` to get contents of bundle to filesystem, unpack and use further.

Note that Upload External API can be replaced with any other service to upload files, since box just fetches contents, 
for example `curl https://raw.githubusercontent.com/python/peps/master/pep-0008.txt` will do the same.



## Box


### Box Version    
***/transport/box/version***    
```javascript
Return current server's version


request (GET):
    params: none
    
response:
30

Note: version return as plain text in body of response

```

### Box Update    
***/transport/box/update***    
```javascript
Return current server's version

request (GET):
    params: 
        id: str = None,                 # box id (usually mac address)
        previous_version: int = None,   # box's current version (usually boxes come here after they define 
                                                        that server has new version of update script for them)
        lat: float = None,              # box's current latititude
        lng: float = None,              # box's current longitiude
        lon: float = None,              # same as 'lng'
        
        # currently not used
        #user: str = None,          
        #region: str = None,
        #network_interface: str = None
    
response:
<update_script_contents>

Note: scripts contents return as plain text in body of response

```



## Admin


### Admin Login
 - See [Login API](../mobile_app/login.md#login)

### Admin Box Update
***/transport/box/v1/admin/update***     
```javascript
Return current server's version

request (GET):
    params: none
    
response:  
    <html form> to make POST on same route
    and current update's content


request (POST):
    multipart/form-data
    params: 
        file: file              # update script's content as file
        apply: bool = False     # should server auto increment its current version
    
response:
    {
      "file": "/transport/box/update",      # route to check if update really applied
      "applied": false,
      "version": "30",                      # server's version after apply (if applied)
      "message": "OK", 
      "status": 200
    }
    
Note: 

```

### Admin Upload External
***/advertisement/v1/admin/upload_external***    
```javascript
*old api from advertisement module*

request (GET):
    params: none
    
response:  
    <html form> to make POST on same route

request (POST):
    multipart/form-data
    params:
        file: file              # contents of uploaded file
    
response:
    {
        "status":200,
        "message":"OK",
        "uploaded_file_url":"http://transport.inobi.kg:5000/advertisement/v1/uploads/external/7bc98a55-45a4-4a56-906b-8d41413a8b44",
        "filename":"7bc98a55-45a4-4a56-906b-8d41413a8b44"
    }

Note: 'uploaded_file_url' key - that is what you need

```

### Admin Box Version
***/transport/box/v1/admin/version***    
```javascript
Return current server's version

request (GET):
    params: none
    
response:  
    <html form> to make POST on same route


request (POST):
    params: 
        version: str        # new server's version
    
response:
    {
      ...
      "message": "OK", 
      "status": 200
    }
   
Note: this API used to directly set just new server's version, 
      in real life it almost not used.

```
