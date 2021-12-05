

create table if not exists transport_organization_notifications (
    id serial primary key,
    organization int not null,
    resolved boolean default false,
    type varchar not null,
    domain varchar not null,
    title varchar not null,
    content varchar not null,
    attributes varchar,
    payload varchar,
    register_time float not null default extract(epoch from now())
);

create index if not exists to_notifications_organization_resolved_idx on transport_organization_notifications (organization, resolved);

do $$
begin
    if not exists(select 1 from information_schema.columns
        where column_name = 'register_time' and table_name = 'transport_organization_notifications') then

        alter table transport_organization_notifications add column register_time float not null default extract(epoch from now());
    end if;
end;
$$;
