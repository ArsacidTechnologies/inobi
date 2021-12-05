
create table if not exists chronicles (
    client_mac varchar null,
    time float not null,
    device varchar null,
    box_mac varchar not null,
    ad_id uuid not null,
    lat float not null,
    lng float not null,
    redirected boolean not null,
    events varchar not null
);
