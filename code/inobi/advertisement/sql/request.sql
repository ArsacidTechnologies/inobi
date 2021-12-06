
CREATE TABLE IF NOT EXISTS request (
    client_mac varchar null,
    time float not null,
    user_agent varchar null,
    box_mac varchar(25) null,
    ad_id uuid not null,
    lat float not null,
    lon float not null
);
