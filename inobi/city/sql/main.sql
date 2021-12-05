

create table if not exists cities (
    id serial primary key,
    name varchar not null,
    lat float not null,
    lng float not null,
    zoom float not null default 12.0,
    lang varchar not null default 'en',
    country varchar null,
    db_version int not null default 1,
    payload varchar default '{}'
);


-- added db_version to city
do $$
begin
    if not exists(select 1 from information_schema.columns
        where column_name = 'db_version' and table_name = 'cities') then

        alter table cities add column db_version int not null default 1;
    end if;
end;
$$;


-- added payload to city
do $$
begin
    if not exists(select 1 from information_schema.columns
        where column_name = 'payload' and table_name = 'cities') then

        alter table cities add column payload varchar default '{}';
    end if;
end;
$$;