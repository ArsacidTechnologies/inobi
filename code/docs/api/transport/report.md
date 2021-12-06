[transport report](#transport-report)   
[driver report](#driver-report)   


### Transport Report   
***/transport/organization/v1/buses/report***   
access roles - transport_admin   
```javascript
request:
    POST
        transports: array, list of transport ids (Required),
        start_date: float, epoch timestamp (Required),
        end_date: float, epoch timestamp (Required)
response:
    start_date: float,
    end_date: float,
    message: str,
    status: int,
    data: array, list of Reports*
```
[Report](#report-structure)
### Generate XLSX file   
***/transport/organization/v1/buses/report/xlsx***   
access roles - transport_admin   
```javascript
request:
    POST
        date: str (Required)
        data: array of Report* (Required)
response:
    XLSX file
```
[Report](#report-structure)

### Driver Report
***/transport/organization/v1/drivers/report***   
access roles - transport_admin   
```javascript
request:
    GET
        driver: int, driver id (Required),
        start_date: float, epoch timestamp (Required),
        end_date: float, epoch timestamp (Required)
response:
    start_date: float,
    end_date: float,
    message: str,
    status: int,
    data: {
        Report*,
        periods: [
            Report*,
            Transport*,
            start_date: float,
            end_date: float,
            payload: {
                issuer: User* (nullable),
                next_driver: int (nullable),
                previous_driver: int (nullable),
                reason: str (nullable),
                time: float, epoch (nullable)
            }
        ]
    
    }
```
[Report](#report-structure)   
[Transport](/docs/api/transport/bus.md#transport-structure)   
[User](/docs/api/mobile_app/login.md#user-type)   


### Report Structure
```javascript
{
    "average_speed": float,
    "max_speed": float,
    "passengers_in": float,
    "passengers_out": float,
    "total_distance": float
}
```  
