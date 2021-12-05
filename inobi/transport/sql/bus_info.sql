create table if not exists bus_info(
    id serial primary key,
    device_id varchar not null,
    lat float not null,
    lng float not null,
    status smallint,
    time bigint not null,
    total_time_on bigint not null
);