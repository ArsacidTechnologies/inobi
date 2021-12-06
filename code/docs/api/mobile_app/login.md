# Application Login API

[Verification](#verification)   
[Login](#login)   
[Registration](#registration)   
[Check Login](#check-login)
[Forgot Password](#forgot-password)



### Verification
***/app/v1/verify [/(phone|email)]***   
--[hybrid params](#hybrid-parameter)--   
```javascript
request:
    params:
        value: str              // phone or email
        code: str = None        // 4-digit string representing code
        check: bool = False   


for /app/v1/verify/phone
    params:
        value: str              // phone or email
        code: str = None        // 4-digit string representing code
        check: bool = False
        national_code: str = None

response:
if 'code' parameter NOT presents, server starts verification process.
And sends sms on phone or email on email address depends on what was
provided. if value was PHONE, then response format is:
    {
        "message": "OK",
        "status": 200,
        "request": {
            "ip": "127.0.0.1",
            "lang": "en",
            "method": "sms",
            "phone": "+996700742181",
            "id": "bmK2xpjKClF2CQ1rhTsCQm9D6aaa4b44"
        },
        "send_code_attempt": {
            "status_code": 704,
            "total_requests": None,
            "block_duration": None,
            "is_blocked": False
        }
    }
if value was EMAIL, response is:
    {
        "message": "OK",
        "status": 200,
        "request": {
            "email": "irsalabd@gmail.com",
            "id": "x3EkPTOZWLMPOChQhjql0vQF22kPjYBr"
        },
        "send_code_attempt": {
            "status_code": 704,
            "total_requests": None,
            "block_duration": None,
            "is_blocked": False
        }
    }


When 'code' parameter PRESENTS and is correct, then responses are:
    {
        "message": "OK",
        "status": 200,
        "verified": {
            "contact": "+996700742181",
            "id": 12,
            "time": 1523428205.04276,
            "type": "phone"
        },
        "verify_code_attempt": {
            "status_code": 704,
            "total_requests": None,
            "block_duration": None,
            "is_blocked": False
        }
    }
OR 
    {
        "message": "OK",
        "status": 200,
        "verified": {
            "contact": "irsalabd@gmail.com",
            "id": 13,
            "time": 1523428705.35601,
            "type": "email"
        }
        "verify_code_attempt": {
            "status_code": 704,
            "total_requests": None,
            "block_duration": None,
            "is_blocked": False
        }
    }
accordingly to verified value and its type

Note: if 'check' parameter is true, and contact was already verified earlier,
    then it will also return verified contact response
```


### Status of verification
***app/v1/timeout/status'***
```javascript
request:
	{
		"value": str  (email or phone)
	}

if value has been tried for verification, the response will be:
	{
		"verify_code_attempt": {
            "status_code": 704,
            "total_requests": None,
            "block_duration": None,
            "is_blocked": False
        },
        "send_code_attempt": {
            "status_code": 704,
            "total_requests": None,
            "block_duration": None,
            "is_blocked": False
        }
	}
```


### Login
***/app/v2/login*** <br />
--[hybrid params](#hybrid-parameters)-- <br />
```javascript
request:
    params:
        pwd: str,
        login: str = None,
        device_id: str = None,          // user device_id (for wi-fi boxes)
        use_device_id: bool = True      // flag to honor device_id param or not
        
        username: str = None,           @Deprecated use 'login' parameter
        email: str = None,              @Deprecated use 'login' parameter
        phone: str = None               @Deprecated use 'login' parameter
    
    Note: username, email, phone parameters are deprecated, use 'login' parameter instead any of them

    // Required ONE OF parameters ('username', contact), but NOT BOTH
    // contact is ('phone' or 'email')
    
response:
    {
      "token": "TOKEN",
      "user": User (*),
      "transport": Transport (*), 
      "transport_organization": Transport Organization (*), 
      "message": "OK",
      "status": 200
    }
    
    Nullables(!): 'transport', 'transport_organization'
```
- [User](#user-type)
- [Transport](#transport-type)
- [Transport Organization](#transport-organization-type)

    
TOKEN has structure:
```javascript
{
    "iat": 123.0,                                   // issued at (jwt)
    "exp": 321.0,                                   // expiration (jwt)
    "scopes": ["some_scope", "another_scope"],      // scopes (list of strs)
    
    "user": [User](#user-type),
    "transport": Nullable([Transport](#transport-type)),
    "transport_organization": Nullable([Transport Organization](#transport-organization-type))
}
```

<br /><br />
***/app/v3/login*** <br />
An API for iranian users redirected from PWA with PHP Backend, only working with phone to check shahkar validation.
--[hybrid params](#hybrid-parameters)-- <br />
```javascript
request:
    params:
        pwd: str,
        login: str = None          
    
response:
    {
      "token": "TOKEN",
      "user": User (*),
      "transport": Transport (*), 
      "transport_organization": Transport Organization (*), 
      "message": "OK",
      "status": 200
    }
    
    Nullables(!): 'transport', 'transport_organization'
```
- [User](#user-type)

    
TOKEN has structure:
```javascript
{
    "iat": 123.0,                                   // issued at (jwt)
    "exp": 321.0,                                   // expiration (jwt)
    "scopes": ["some_scope", "another_scope"],      // scopes (list of strs)
    
    "user": [User](#user-type),
    "transport": Nullable([Transport](#transport-type)),
    "transport_organization": Nullable([Transport Organization](#transport-organization-type))
}
```


### Registration
***/app/v2/register*** <br />
--[hybrid params](#hybrid-parameters)-- <br />
```javascript
request:
    params:
        name: str,
        email: str = None,
        phone: str = None,
        birthday: float = None,                         // birthday (in seconds from epoch)
        national_code: str = None,
        gender: int = None, 
        payload: dict = None,                           // any other user data can be put here
        username: str(>=3) = None,                      
        pwd: str(>=6) = None,                           // password
        type: str(enum of 'google', 'facebook') = None, // type of token
        token: str = None,                              // token of socials
        jwt: str = None                                 // alias to 'token'
    
    - at least email or phone MUST present and at least one of them must be VERIFIED (look at verification section)
    - at least one of credentials MUST present: (username and pwd) or (type and token)
    

response:
    {
      "token": "TOKEN",
      "user": User (*),
      "transport": Transport (*), 
      "transport_organization": Transport Organization (*), 
      
      "message": "OK",
      "status": 200
    }
```
- [User](#user-type)
- [Transport](#transport-type)
- [Transport Organization](#transport-organization-type)



### Check Login
***/app/v1/login/check***   
--[hybrid params](#hybrid-parameter)--   
```javascript
request:
    params:
        value: str                      // phone or email
        region: str = APP_REGION        // 2-char string representing region, default 'KG' for Kyrgyzstan and 'IR' for Iran


response:
    {
      "is_registered": true, 
      "is_verified": true, 
      "is_shahkar_verified": true, 
      "message": "OK", 
      "region": "KG", 
      "status": 200, 
      "type": "phone", 
      "value": "+996700742181"
    }

    OR
    
    {
      "is_registered": false, 
      "message": "OK", 
      "status": 200, 
      "type": "email", 
      "value": "irsalabd@gmail2.com"
    }
    
    OR 
    
    {
      "error": "Value Must Be A Valid Phone Number or Email Address", 
      "error_code": 746, 
      "status": 400
    }
```


### Forgot password   
***/app/v1/restore_access***   
--[hybrid params](#hybrid-parameter)--   
```javascript
request:
    params:
        - contact: str              // phone or email
        - code: str = None          // 4-digit string 
        - new_pwd: str = None       // 6 or more character length string

response:

Beware, this API redirects to verify API

If only 'contact' present, will send verification code on it
If 'contact' was PHONE, then response format is:
    {
        "message": "OK",
        "status": 200,
        "request": {
            "ip": "127.0.0.1",
            "lang": "en",
            "method": "sms",
            "phone": "+996700742181",
            "id": "bmK2xpjKClF2CQ1rhTsCQm9D6aaa4b44"
        }
    }
If 'contact' was EMAIL, response is:
    {
        "message": "OK",
        "status": 200,
        "request": {
            "email": "irsalabd@gmail.com",
            "id": "x3EkPTOZWLMPOChQhjql0vQF22kPjYBr"
        }
    }
    


If 'code' parameter presents, then 'new_pwd' parameter MUST PRESENT too.

The main success response is:
    {
      "login": {
        "id": 1, 
        "register_time": 1520243035.62744, 
        "username": "RisAbd"
      }, 
      "message": "OK", 
      "prev": {
        "id": 1, 
        "register_time": 1520243035.62744, 
        "username": "RisAbd"
      }, 
      "status": 200
    }
    
    ...means: "Your password is changed"

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


### User Type
```javascript
{      
    "id": 1, 
    "register_time": 1519397483.14643, 
    
    "username": "RisAbd", 
    "name": "Abdullah Ibragimov"
    "email": "irsalabd@gmail.com",  
    
    "phone": "0772313968", 
    "birthday": 123.0,                      // birthday as epoch! time
    "national_code": "4181067280",          // Iranian national id
    "payload": {},                          // some additional info  
    
    // most likely will not be in response
    // "device_id": "f5:00:13:e6:aa:01",       // mac address of user (used to login through wifi-boxes)
    
    "social_user": {                        // NULLABLE
      "id": 1,                              // id of social_user registered alongside this user
      "register_time": 1523424789.81631
      "sid": "1603078739738352",            // socials identifier
      "type": "facebook",                   // socials type
      "payload": {}                         // some socials payload (not really interesting, but some info can be retrived if necessary)
    }
    
    "login": {                              // NULLABLE
      "id": 60,                           // id of login
      "register_time": 1523424789.81631,
      "username": "Username"              
    }
  }
```


### Transport Type
*--reference to transport docs to get detailed info about this type*
```javascript
{
    "id": 258,
    "line_id": 1382,            // identifier of line(aka route)
    "independent": true,        // defines if its driver-dependent device
    "device_id": "5555",        // id which can be accepted by /transport/bus directly
    "device_phone": null,       // phone number of device
    "driver": 2,                // driver id (nullable)
    "name": "B1526B",           // name of device
    "payload": null             // additional info about device
}
```


### Transport Organization Type
```javascript
{
    "id": 1, 
    "name": "Inobi",                
    "traccar_username": "inobi",    // Traccar username for organization            
    "payload": {}
}
```
