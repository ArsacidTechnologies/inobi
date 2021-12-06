
# API
-- unsecured/public    
[Cities List API](#cities-list)   
[Single City API](#single-city)   
[City Data Version API](#city-data-version)    
[City Data API](#city-data)    
-- transport organization managers    
[City Upgrade API](#city-data-upgrade)    
[City Upgrade Apply API](#city-data-upgrade-apply)


## Cities

### Cities List    
***/v1/cities***    
```javascript
request (GET):
    params: none
    
response:
    {
      "cities": [ City* ], 
      "message": "OK", 
      "status": 200
    }
```
 - See [City Type](#city-type)


### Single City     
***/v1/cities/<city_id:int>***   
**OR**   
***/v1/city?id=<city_id:int>***
```javascript
request (GET):
    city_id: int
    
response:
    {
      "city": City(*), 
      "message": "OK", 
      "status": 200
    }
```
See [City Type](#city-type)


## City Data (public API)

### City Data Version   
***/v1/cities/<city_id:int>/data/version***   
**OR**   
***/v1/city_data_version?id=<city_id:int>***
```javascript
request (GET):
    city_id: int
    
response:
    {
        "message": "OK",
        "status": 200,
        "version": 1
    }
```


### City Data   
***/v1/cities/<city_id:int>/data/<data_version:int>***   
**OR**   
***/v1/city_data?city=<city_id:int>&version=<data_version:int>***
```javascript
request (GET):
    city_id:        int
    data_version:   int
    
response:
    <Zip-archive of database of city in BINARY format>
    <with 'data.db' file inside containing all data  >
```

## City Data (transport organizations API)

### City Data Upgrade   
***/v1/cities/<city_id:int>/upgrader***    
-- @secured( >= **transport_admin**)    
```javascript
-- get list of city databases/processes running
request (GET):
    city_id: int
    
response:
    {
        "message": "OK",
        "status": 200,
        "processes": [CityDataUpgrade](*)
    }
    
-- initiate new upgrade process (new database generation)
request (POST):
    city_id: int
    
response:
    {
        "message": "OK",
        "status": 200,
        "process": CityDataUpgrade(*)
    }
```   
See [City Data Upgrade Type](#city-data-upgrade-type)


### City Data Upgrade Apply
***/v1/cities/<city_id:int>/upgrader/<process_name:str[uuid]>/***      
-- @secured( >= **transport_admin**) (*temporarily*, will require **transport_inobi**)    
```javascript
-- get databases/processes by id (name)
request (GET):
    city_id: int
    process_name: [uuid]str
    
response:
    {
        "message": "OK",
        "status": 200,
        "process": CityDataUpgrade](*)
    }

-- apply databases/processes to city (application will detect database change and download new data)
request (POST):
    city_id: int
    process_name: [uuid]str
    
response:
    {
        "message": "OK",
        "status": 200,
        "process": CityDataUpgrade(*),
        "applied": true
    }
```   
See [City Data Upgrade Type](#city-data-upgrade-type)


## Response Types

#### City Type
```json
{
  "country": {                  // maybe any json
    "calling_code": "996", 
    "code": "KG", 
    "name": "Kyrgyzstan"
  }, 
  "db_version": 1,              // version of city database
  "payload": {},                // any other data stored here
  "id": 1, 
  "lang": "ky",                 // 2-char string
  "location": {                 
    "lat": 42.87911, 
    "lng": 74.61275, 
    "zoom": 12.0
  }, 
  "name": "Bishkek"
}
```



#### City Data Upgrade Type
```json
{
	"name": "54213b56-bf68-4bcb-957e-254e0d73766d",	  // aka process id
	"city": "2",
	"organization": "2",
	"user": "101",								// user initiated upgrade request
	"stage": "processing",		// stage of process (str, enum of ('init', 'processing', 'done'))
	"file": {					// nullable in POST request
		"modified": 1539074803.892992,
		"accessed": 1539074803.9099925,
		"size": 131072
	},
	"process": {				// nullable
		"pid": 32,
		"start_time": 1539074802.7873065
	},
	// debug
	"_fn": "54213b56-bf68-4bcb-957e-254e0d73766d.c2.to2.u101.db.processing",
	"_fp": "resources/city/dbupgrader/54213b56-bf68-4bcb-957e-254e0d73766d.c2.to2.u101.db.processing"
}
```
