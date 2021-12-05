


create table if not exists messages (
    id serial primary key,
    register_time float not null default extract(epoch from now()),
    issuer varchar not null,
    service varchar null,
    "type" varchar not null,
    "to" varchar null,
    content varchar not null
);
