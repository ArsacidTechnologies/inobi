inobi
=========

----------
Wi-Fi Box API 
----------

(**Required** parameters,

*Eligible* parameters,

Optional parameters)


####**/box/version** {get}
> Send parameters:
> > {

> > }
> > * No parameters  
>
> Response:
> > **an integer presenting current update version**
> > * '-1' can be returned if Any error was occured on server side
>


####**/box/update** {get}
> Send parameters:
> > {

> > *"id"*: "00:00:00:00:00:00",

> > "*prev_ver*": "*some_identifier(mostly integer)*",

> > "*lat*": some_latitude,

> > "*lon*": some_longitude

> > }
> > * If request will contain empty body, still will an update instructions returned. But STRONGLY RECOMMENDED to send all info you can.
>
>  Response:
> > **an instructions as plain text**
> > * save it and execute to update box to current version
>


####**/v1/admin/box/updates** {get}
> Send parameters:
> > {

> > }
>
>  Response:
> > {

> > *"count"*: (null or *some_int*),

> > **"updates"**: **[

> > ...   *some_update_infos*[^update_info]

> > ]**,

> > **"message"**: "OK",

> > **"status"**: 200

> > }
>



####**/box/internet** {get}
> Send parameters:
> > {

> > }
> > * No parameters  
>
> Response:
> > **1** or **0**
> > * *1* means permission given, *0* - not given
>


####**/v1/admin/box/internet** {get, post}
> If **GET** request, will be **redirected** to **/box/version**
> Send parameters:
> > {

> > **"allow"**: *some_string*

> > }
> > * **allow** must be any of ['true', 'false', 'on', 'off', 'allow', 'not_allow', 'notallow'] in any case
>  
> Response:
> > {

> > **"message"**: "OK",

> > **"status"**: 200

> > }
>


####**/v1/admin/box/version** {get, post} DISABLED FOR SECURITY PURPOSES
> If **GET** request, will be **redirected** to **/box/version**
> Send parameters:
> > {

> > **"version"**: some_int

> > }
> > * parameters can be sent as post argument in url ("../v1/admin/box/version?version=1" like)
> 
> Response:
> > {

> > **"previous_version"**: (null or *some_int*),

> > **"current_version"**: *some_int*,

> > **"message"**: "OK",

> > **"status"**: 200

> > }
>


####**/v1/admin/box/upload_update** {get, post}  DISABLED FOR SECURITY PURPOSES
> **GET** request will return following form
> ```
> <form action="/v1/admin/box/upload_update" method=post enctype=multipart/form-data>
> <input type=file name=file>
>   <label><input type=checkbox name=apply checked>Apply update</label>
>   <input type=submit value=Upload>
> </form>
> ```
>
> **POST**
> Response:
> > {

> > **"message"**: "OK",

> > **"status"**: 200,

> > **"applied"**: *some_boolean*,  

> > **"file"**: "http://../box/update"

> > }
> > * applied is true if checkbox in *form* were checked. If applied then will increase current **update version** to 1, so boxes will update themselves.
> > * *file* is just full url to /box/update
> > * * Error will be returned if file not selected or some server error occured
>


----------

 [^update_info]:
> { 

> ***id, previous_version, version, time, lat, lon***

> }
>

