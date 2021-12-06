### send mail   
***/transport/organization/v1/mail***    
access roles - transport_viewer    
```javascript
POST:
    params:
        to_address: str, list // REQUIRED
        subject: str          // REQUIRED
        message: str          // REQUIRED
        
        attachment: str, list // OPTIONAL | filename(s)
        attachment_type: str  // OPTIONAL, but REQURIED when attachment presents | type of the attachment e.g. report
        report: dict          // OPTIONAL, but REQUIRED when attachment_type = report and attachment not presented 
    
    response:
        OK
```