
# API   
-- advertisement admins    
[Transport statistics API](#transport-statistics)    
[User views statistics API](#user-views-statistics)    
[User registration statistics API](#user-registration-statistics)     
[Total uniques count API](#total-uniques-count)


## Transport

### Transport statistics    
***/advertisement/v1/admin/stats/transports/***    
```javascript
Returns array of transports statistics.


request (GET/POST):
    params: 
	start: float 				// unix time
	end: float 				// unix time
	cities: [int] = null			// city ids  
	organizations: [int] = null 		// transport organization ids
    
    min_hour: int = 5               // hour to group views that lower than value
    max_hour: int = 21              // hour to group views that upper than value
    
response:
    {
      "stats": [ TransportStatistics* ], 
      "no_views": [ TransportStatistics* ],
      "hour_stats": [ HourStatistics* ],
      "message": "OK", 
      "status": 200
    }
```
 - See [Hour Statistics Type](#hour-statistics-type)
 - See [Transport Statistics Type](#transport-statistics-type)


## User

### User views statistics    
***/advertisement/v1/admin/stats/users/views/***    
```javascript
Return array of advertisement user stats.
- paginated


request (GET/POST):
    params: 
    	start: float 				// unix time
    	end: float 				// unix time
    	cities: [int] = null			// city ids  
        organizations: [int] = null 		// transport organization ids
        limit: int = 10 			// pagination limit parameter
	    offset: int = 0 			// pagination offset parameter
    
response:
    {
 	"pagination": {
		"count": 10,
		"total_count": 5347,
		"params": {
			"prev": null,
			"next": {
				"start": 1539108000.0,
				"end": 1539626400.0,
				"limit": 10,
				"offset": 10
			}
		},
		"url": {
			"prev": null,
			"next": "http://localhost:5000/advertisement/v1/admin/stats/users/?start=1539108000.0&end=1539626400.0&limit=10&offset=10"
		}
  	}
	"stats": [ UserViewStatistics* ], 
	"message": "OK", 
	"status": 200
    }
```
 - See [User Views Statistics Type](#user-views-statistics-type)   


### User registration statistics    
***/advertisement/v1/admin/stats/users/registrations/***    
```javascript
Return array of advertisement user stats.
- paginated


request (GET/POST):
    params: 
        phone: str = None                   // phone to search in database with like statement '%{phone}%'
    	registered_start: float = None      // unix time
    	registered_end: float = None        // unix time
    	cities: [int] = null			// city ids  
        organizations: [int] = null 		// transport organization ids
        limit: int = 10 			// pagination limit parameter
        offset: int = 0 			// pagination offset parameter
        
    * at least one of filters MUST be specified.
    possible filters:
        - 'phone'
        - 'register_start' and 'register_end'
    
response:
    {
 	"pagination": {
		"count": 10,
		"total_count": 5347,
		"params": {
			"prev": null,
			"next": {
				"start": 1539108000.0,
				"end": 1539626400.0,
				"limit": 10,
				"offset": 10
			}
		},
		"url": {
			"prev": null,
			"next": "http://localhost:5000/advertisement/v1/admin/stats/users/?start=1539108000.0&end=1539626400.0&limit=10&offset=10"
		}
  	}
	"stats": [ UserRegistrationStatistics* ], 
	"message": "OK", 
	"status": 200
    }
```
 - See [User Registration Statistics Type](#user-registration-statistics-type)   


### Total uniques count    
***/advertisement/v1/admin/stats/users/uniqueness/***    
```javascript
Returns count of total unuque users.

request (GET/POST):
    params: 
    	start: float = None         // unix time
    	end: float = None           // unix time
    
response:
    {
	"stats":{
		"total_uniques": 12339
	}, 
	"message": "OK", 
	"status": 200
    }
```


## Response Types

#### Transport Statistics Type
```javascript
{
	"id": 119,						// transport id
	"name": "325",						// transport name
	"device_id": "00:0b:6a:21:54:1e",			// transport device id
	"route_id": 680,					// transport route id
	"route_name": "8",					// transport route name
	"city_id": 1,						// transport city id
	"city_name": "Qazvin",					// transport city name
	"transport_organization_id": 1,				// transport org. id 
	"transport_organization_name": "ARA",			// transport org.name
	"date": "2018-10-10",					// date of statistics (nullable for no_views transports) 
	"views": 103						// count of views for transport (nullable for no_views transports) 
}
```


### Hour Statistics Type
```javascript
{
    "hour": 14,
    "transports": 29.3333333333333,     // average
    "views": 104.666666666667,          // average
    "days": 3
}
```


#### User Views Statistics Type
```javascript
{
	"id": 11125,					// user id
	"phone": "+989333444888",			// user phone
	"registered": 1539622194.35232, 		// registered date (unix)
	"views": 1,					// views count
	"devices": 1,					// devices count
	"first_view": 1539622198.24035,			// first view date in given range (unix)
	"last_view": 1539622198.24035			// last view date in given range (unix)
}
```


### User Registration Statistics Type
```javascript
{
    "id": 10600,
    "phone": "+989333999123",
    "registered": 1539504189.546748,
    "login_time": 1539504189.5498,
    "device": {
        "id": 10722,
        "mac": "00:ae:fa:7f:07:bf",
        "description": "Linux; Android 6.0.1; SAMSUNG SM-N910C Build/MMB29K"
    },
    "view": {                                                    // nullable
        "v_id": 53123
        "ad_id": "6e5714f6-19fc-42c4-883b-2046a988d9e6",
        "redirected": true,
        "lat": 36.29394367,
        "lng": 0.0,
        "transport": {                                           // nullable
            "t_id": 113,
            "t_name": "327",
            "line_id": 680,
            "line_name": "8"
        }
    }
}
```