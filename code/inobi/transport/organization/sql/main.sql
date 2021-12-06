

do $$
-- try not to touch it
declare DO_CLEANUP boolean = false;
begin
    if DO_CLEANUP then
        drop table if exists transport_organization_lines;
        drop table if exists transport_organization_drivers;
        drop table if exists transport_organization_admins;
        drop table if exists transport_organization_transports;
        drop table if exists transport_organizations;
    end if;
end
$$;


create table if not exists transport_organizations (
    id serial primary key,
    name varchar not null check (length(name) > 2),
    traccar_username varchar unique not null,
    traccar_password varchar not null,
    payload varchar not null default '{}',
    city int not null,
    settings json null
);


-- removing region, lat, lng zoom columns
--do $$
--begin
--    if exists(select 1 from information_schema.columns
--        where column_name in ('region', 'lat', 'lng', 'zoom', 'lang') and table_name = 'transport_organizations' ) then
--
--        alter table transport_organizations drop column country;
--        alter table transport_organizations drop column lat;
--        alter table transport_organizations drop column lng;
--        alter table transport_organizations drop column zoom;
--        alter table transport_organizations drop column lang;
--
--    end if;
--end;
--$$;
--
--
---- added city columns
--do $$
--begin
--    if not exists(select 1 from information_schema.columns
--        where column_name = 'city' and table_name = 'transport_organizations') then
--
--        alter table transport_organizations add column city int not null default 1;
--
--        ALTER TABLE transport_organizations ALTER COLUMN city DROP DEFAULT;
--
--    end if;
--end;
--$$;
--
--
---- rename notification_settings -> settings
--do $$
--begin
--    if exists(select 1 from information_schema.columns
--        where column_name = 'notification_settings' and table_name = 'transport_organizations') then
--
--        alter table transport_organizations rename notification_settings to settings;
--    end if;
--end;
--$$;
--
---- added settings column
--do $$
--begin
--    if not exists(select 1 from information_schema.columns
--        where column_name = 'settings' and table_name = 'transport_organizations') then
--
--        alter table transport_organizations add column settings json null;
--    end if;
--end;
--$$;

create table if not exists transport_organization_lines (
    "organization" int not null,
    "line" int not null

--    foreign key (organization) references transport_organizations(id),
--    foreign key (line) references routes(id)
);
--
--create table if not exists transport_organization_stations(
--    "organization" int not null,
--    "station" int not null
--);
--
--create table if not exists transport_organization_directions(
--    "organization" int not null,
--    "direction" int not null
--);
--
--create table if not exists transport_organization_platforms(
--    "organization" int not null,
--    "platform" int not null
--);


create table if not exists transport_organization_admins (
    "organization" int not null,
    "user" int not null

--    foreign key (organization) references transport_organizations(id),
--    foreign key ("user") references users(id)
);


create table if not exists transport_organization_drivers (
    "organization" int not null,
    "user" int not null

--    foreign key (organization) references transport_organizations(id),
--    foreign key ("user") references users(id)
);


create table if not exists transport_organization_transports (
    "organization" int not null,
    "transport" int not null unique

--    foreign key (organization) references transport_organizations(id),
--    foreign key (transport) references transports(id)
);

