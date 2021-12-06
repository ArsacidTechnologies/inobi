/v1/register/chronicles/

**`header`**:

    {
        'user_agent': str,
        'device_id': str,
    }
	
<hr/>

**`parameters`**:

    {
        'ad_id': uuid (str) # id of ad
        'lat': float,
        'lon': float,
        'box_mac': str,
        'redirected': bool,
        'events': str,
    }

<hr/>

**`response`**:

    {
        'status': 200
        'message': str,
        'chronicle': {
            'id': int,            # id of created chronicle
            'ad_id': uuid (str),  # id of ad that chrnocile is related to
            'client_mac': str  (device_id from header - to find ads_device_id),
            'time': float (epoch),
            'device': str (user_agent from header),
            'box_mac': str,
            'lat': float,
            'lng': float,
            'redirected': bool,
            'events': str,
            'ads_device_id': int (id of AdDevice gotten with client_mac which is related to AdUser),
        }
    }

<hr/>

**`error_response`**:

if `box_mac` is not null and is not valid

    {
        message='Box MAC is not valid',
        error_code= 1019 (BOX_MAC_NOT_VALID),
        status=400
    }

if `device_id` in header, is not null and is not valid

    {
        message='Mac address is not valid',
        error_code= 1013 (MAC_ADDRESS_NOT_VALID),
        status=400
    }
    
if `ad_id` in header, is null,

    {
        message='`ad_id` parameter is not present.',
        error_code= 1020 (AD_ID_NOT_PRESENT),
        status=400
    }
