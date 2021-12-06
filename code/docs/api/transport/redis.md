[delete unknown](#delete-unknown)

### Delete
***/redis/delete***
```
request:
    GET
        Headers:
            {"Authorization": "Bearer {TOKEN}"}
        params:
            segment = all || unknown || lines || buses
response
    {
        "message": "OK",
        "status": 200
    }
```