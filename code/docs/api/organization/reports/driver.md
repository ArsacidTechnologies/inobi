### driver report
***/transport/organization/v1/drivers/report***   
access roles - transport_admin   
pass JWT in [params](#hybrid-parameters)
```javascript
request
    GET
        "driver": int (Required)
        "start_date": int, float (Required) [timestamp]
        "end_date": int, float (Required) [timestamp]
response
    "data": dictionary = 
     {
        "passengers_in": int, float - total count of passengers in transport
        "passengers_out": int, float - total count of passengers out transport
        "periods": array of dictionaries = 
        [
            {
                "passengers_in": int, float - period count of passengers in transport
                "passengers_out": int, float - period count of passengers out transport
                "start_date": int, float - timestamp
                "end_date": int, float - timestamp
                "transport": *Transport
                "points": array of dictionaries =
                [
                    {
                        "course": float
                        "lat": float
                        "lng": float
                        "time": float
                        "payload": dict - extra data
                    }
                ]
                "payload": dict - extra data = 
                {
                    "issuer": int - id of user who changed
                    "previous_driver": int (null)
                    "next_driver": int (null)
                    "reason": str (null)
                    "time": int, float - timestamp
                }
            }
        ]
    },
    "message": str,
    "status": int
```
[Transport](/docs/api/transport/bus.md#transport-structure)   

