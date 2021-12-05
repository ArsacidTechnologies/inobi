
create table if not exists box_updates (
    id varchar(25) primary key not null,
    previous_version varchar null,
    version varchar not null,
    "time" float not null,
    lat float,
    lng float
);

alter table box_updates alter column lat drop not null;
alter table box_updates alter column lng drop not null;

