# Overview
Advertisement view process starts with [fetching an ad info](#random-ad). <br />
Application `platform` and its id (`provider_id`) SHOULD be sent, if available viewer location can be sent too. <br />
API can return 404, that means no ads available by sent criterion (or ads disabled on server). In this case ad is not shown. <br />
After fetching ad, its source must be downloaded (`view.ad.source_full`). <br />
Its content must be shown to user according to ad settings. <br />
Ad can be `banner`, `video` or `iframe` type. <br />
Ad's `duration` describes amount of time that ad must be on user's screen.
View should not be registered until at least `duration` amount of time ad wasn't shown on user's device. <br />
`redirect_url` contains url where user should be redirected when intented to (ex.: taps banner after duration, or clicks video, etc.) <br />
When view process is over view must be [registered](#register-view). <br />
User's id (or device id), result of view (redirect or skip), platform, events and other useful information (see [View Type](#view-type))
should be sent when registering view.


## API
[Random Ad](#random-ad) <br />
[Register View](#register-view)


### Random Ad
***/advertisement/v1/ads/random*** <br />
access roles - none <br />
--[hybrid params](#hybrid-parameters)-- <br />
```javascript
request:
    params:
        lat: float = None,                                                      // latitude of requester
        lng: float = None,                                                      // longitude of requester
        platform: enum of ('ios', 'android', 'wifi', 'mobile', 'all', 'box') = 'all'   // platform of requester (default 'all')
        display_type: enum of ('fullscreen', 'list-item') = 'fullscreen'        // to filter ads by its display type
        provider_id: str = None                         // id of app instance (or box id, like MAC-address)
        test: bool = false
        only_unvisited = false
response:
    {
      "ad": [Ad](#ad-type),
      "skip_timer": int,
      "view_token": "68e58be2-aa83-4198-a6a9-e8edb6adecd2",
      "message": "OK",
      "status": 200
    }
```
if `only_unvisited` and `client_mac` provided, then will go through random ads with priority of ads which user with this client_mac didn't vitst yet.

### Register View
***/advertisement/v1/views/*** <br />
access roles - advertisement_ad_viewer <br />
--[hybrid params](#hybrid-parameters)-- <br />
```javascript
request:
    POST:
        params:
            token: str                         // (required) string value from #random-ad request
            device_id: str,                         // (required) id of viewer or his device
            is_redirected: bool,                    // (required) is result of view was redirect
            platform: str = 'wifi',                 // see #platform-type
            provider_id: str = None,                // id of app (in case of app view) or
            events: list = None,                    // array of events (see #view-type)
            device_description: str = None,         // viewer description (or his device, like HTTP User-Agent header)
            lat: float = None,                      // latitude of view (if available)
            lng: float = None,                      // longitude of view (if available)
            view_time: int = None,                  // unix timestamp of actual view (if not passed request time will be used instead)
            test: Modifier.BOOL = False             // debug param

response:

    {
        "message": "OK",
        "status": 200,
        "view": [View](#view-type)
    }
```


## Hybrid Parameters
Hybrid parameters are parameters that can be sent as GET arguments
or as root attributes in JSON in POST-request's body <br />
Example: <br />
`?some=value&another=maybe`

is same as

```
{
  "some": "value",
  "another": "maybe"
}
```

***Note***: Some arguments in endpoints are required to be complex objects
and can not be described as GET argument, like arrays or nested objects. In this cases POST request must be
performed (since somehow those object must be sent)<br />
\#(todo: objects as get-args)


## Types
### Ad Type
```javascript
Ex. 1:
{
    "created": 1495775844.69884,    // float (unix-time in seconds)
    "description": "Banner",        // str
    "duration": 10.0,               // float (recommended duration for ad)
    "enabled": true,                // bool
    "expiration_date": null,        // todo: ad date expiration
    "external_source": false,       // bool (is source hosted outside of server)
    "id": "8201e486-6cc5-4048-9e7f-9482b7893124",   // str (uuid-like identifier)
    "lat": null,                    // float (latitude) | todo: geotargeting
    "lon": null,                    // float (longitude) | todo: geotargeting
    "redirect_url": "teztaxi.kg",   // str (url to redirect in case user interested in ad, aka. 'click')
    "requests": 565630,             // int (ad requests through public endpoints)
    "source": "e93bb622-466f-484f-a293-b4945cc42cdb.png",   // str (source name)
    "source_full": "http://localhost:4325/advertisement/media/e93bb622-466f-484f-a293-b4945cc42cdb.png",
    "title": "Tez",                 // str
    "type": "banner",               // enum of ("banner", "video", "iframe") (type of ad)
    "views": 185532,                // int (ad registered views)
    "views_max": null,              // todo: ad views expiration
    "weight": 2,                    // int (weight of ad, more weight -> more it will be seen when requested)
    "display_type": "fullscreen"
}

Ex. 2:
{
    "id": "65944aa1-3d0d-4da3-baff-5e140a258d6c",
    "type": "banner",
    "duration": 8.0,
    "redirect_url": "inobi.kg",
    "weight": 1,
    "views": 2,
    "source": "25f69352-475b-40dd-9279-a872a33a1d7a.png",
    "created": 1556081397.8433,
    "enabled": true,
    "title": "kek",
    "description": "mek",
    "lat": null,
    "lng": null,
    "views_max": null,
    "expiration_date": null,
    "requests": 4,
    "platform": "all",
    "radius": 0.5,
    "cities": null,
    "time_from": null,
    "time_to": "16:00:11",
    "start_date": null,
    "external_source": false,
    "_source": "25f69352-475b-40dd-9279-a872a33a1d7a.png",
    "transport_filters": null,
    "device_filters": [
        "g2"
    ],
    "source_full": "http://localhost:5000/advertisement/media/25f69352-475b-40dd-9279-a872a33a1d7a.png",
    "display_type": "fullscreen"
}
```

### View Type
```javascript
{
    "id": 10,
    "ad_id": "65944aa1-3d0d-4da3-baff-5e140a258d6c",    // id of viewed ad
    "ad": { Ad... },                                    // ad object
    "key": "d12e234e-5374-4afc-9478-31424f1bad94",      // view token
    "created": "Thu, 25 Jul 2019 08:25:39 GMT",         // timestamp of view token created
    "time": "Thu, 25 Jul 2019 14:25:46 GMT",            // timestamp of actual user view
    "is_evaluated": true,                               // read-only, is view happened (did view registered)
    "platform": "all",,                                 // platform view performed
    "provider_id": "kg.inobi.driver",                   // id of app or wifi box instance
    "lat": 123.0,
    "lng": 321.0,
    "is_redirected": true,                              // result of ad view,
    "events": [                                         // list of events
      {
        "type": "INIT",
        "time": 0.0
      },
      {
        "type": "AD_REQUEST_FINISHED",
        "time": 0.63,
      },
      {                                                 // where every item is an object
        "time": 2.234,                                  // Every event SHOULD contain fields:
        "type": "AD_SOURCE_LOADED",                     // "type" describing type of event
        "loading_interval": 1.87,                       // "time" describing seconds passed from start of view process
      },                                                // ... other fields containing useful information would be appreciated
      {
        "time": 3.567,
        "type": "STARTED"
      },
      {
        "type": "USER_GESTURE",
        "time": 5.67,
        "gesture_type": "tap",
        "tap_point": {
            "x": 0.5,   // 0 is lower bound of content viewport
            "y": 0.67   // 1 is upper bound
        }
      },
      {
        "type": "BLA_BLA",
        "time": 10.55
      },
      {
        "time": 15.9,
        "type": "RESULT_REDIRECT",
        "through": "CONTENT_CLICKED",
        "intent_handler": "com.google.chrome"
      },
      {
        "type": "RETURN_AFTER_REDIRECT",
        "time": 48.3
      }
    ],
    "viewer_id": 1,                                     // database id of viewer
    "viewer": {                                         // viewer object
      "id": 1,
      "device_id": "00:00:00:00:00:01",                 // viewer device's id
      "device_description": "Ubuntu 16.04, Linux"       // description of viewer or his device
    },
    "ads_device_id": null,                              // kek
    "ads_group_id": null                                // mek
  }
```

### Platform Type
```javascript
Enum type:
    - android
    - ios
    - wifi
    - box
    - mobile
    - all

#class Platform:
#    WIFI = 1
#    ANDROID = 2
#    IOS = 4
#    BOX = 8

#    MOBILE = IOS | ANDROID
#    ALL = BOX | WIFI | ANDROID | IOS

#    _STR_PLATFORMS = {
#        'android': ANDROID,
#        'ios': IOS,
#        'wifi': WIFI,
#        'all': ALL,
#        'mobile': MOBILE,
#        'box': BOX,
#    }
```
