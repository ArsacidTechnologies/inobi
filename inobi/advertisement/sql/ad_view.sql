
CREATE TABLE IF NOT EXISTS ad_views (
    client_mac varchar null,
    time float not null,
    user_agent varchar null,
    box_mac varchar(25) not null,
    ad_id uuid not null,
    lat float not null,
    lng float not null
);


do $$
begin
    if exists(select * from information_schema.columns
                where table_name = 'app_ad_view'
                    and column_name = 'user'
                    and data_type = 'uuid') then
        drop table if exists app_ad_view;
    end if;
end;
$$;

create table if not exists app_ad_view (
    ad_id uuid not null,
    "user" int null,
    device_id varchar not null,   -- device identificator (taken from iOS/Android OS)
    lat float null,
    lng float null,
    time float not null,
    platform varchar not null,    -- (app bundle_id, os, app_version and build as JSON). Ex. {{"bundle_id": "kg.avisa.inobi", "platform": "android", "version": "2.0", "build": 17}}
    result varchar,               -- aka 'redirected'
    payload varchar null          -- additional info as JSON
);

