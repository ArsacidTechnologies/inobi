
-- migrate db from t_* versions to normal
do $$
begin

    if exists(select * from information_schema.tables
        where
            table_catalog = CURRENT_CATALOG and table_schema = CURRENT_SCHEMA
            and table_name = 't_users') then

        drop table if exists users;
        drop table if exists app_logins;
        drop table if exists social_users;

        alter index t_social_users_type_id_index
            rename to social_users_type_id_index;
        alter index t_user_logins_type_login_index
            rename to user_logins_type_login_index;
        alter table t_users
            rename to users;
        alter table t_social_users
            rename to social_users;
        alter table t_logins
            rename to logins;
        alter table t_user_logins
            rename to user_logins;

        alter sequence t_logins_id_seq
            rename to logins_id_seq;
        alter sequence t_users_id_seq
            rename to users_id_seq;
        alter sequence t_social_users_id_seq
            rename to social_users_id_seq;

    end if;

end;
$$;


-- migrate db from email unique to phone or email contstrainted version
do $$
begin
    if exists(select constraint_name from information_schema.constraint_column_usage
        where constraint_name = 't_users_email_key') then

        alter table users drop constraint t_users_email_key;
        alter table users alter column email drop not null;

        alter table users add constraint users_email_key unique (email);

        update users set phone = null where trim(phone) = '';

        alter table users add constraint users_phone_key unique (phone);
        alter table users add constraint email_or_phone_presents check (email is not null or phone is not null);

    end if;
end;
$$;


create table if not exists users (
    id serial primary key,
    register_time float not null default extract(epoch from now()),
    email varchar null unique,
    name varchar not null,
    phone varchar null unique,
    scopes varchar not null default '[]',
    birthday float null,
    gender smallint null,
    national_code varchar null,
    payload varchar not null default '{}',
    device_id varchar,  -- MAC address
    check (email is not null or phone is not null)
);


-- added device_id column
do $$
begin
    if not exists(select 1 from information_schema.columns
        where column_name = 'device_id' and table_name = 'users' ) then

        alter table users add column device_id varchar;
    end if;
end;
$$;


-- added case-insensitive index on device_id column
create index if not exists users_device_id_idx on users (lower(device_id));


create table if not exists social_users (
    id serial primary key,
    register_time float not null default extract(epoch from now()),
    type varchar not null,
    sid varchar not null,
    payload varchar not null,
    constraint social_users_type_id_index unique (type, sid)
);


create table if not exists logins (
    id serial primary key,
    register_time float not null default extract(epoch from now()),
    username varchar not null unique,
    pwd varchar not null
);


-- username must be case-insensitive column
do $$
begin
    if exists(select 1 from information_schema.constraint_column_usage
        where constraint_name = 't_logins_username_key') then

        alter table logins drop constraint t_logins_username_key;
        create unique index logins_username_key on logins (lower(username));

    end if;
end;
$$;


create table if not exists user_logins (
    "id" serial primary key,
    "login" int not null,
    "user" int not null,
    "type" varchar not null,
    constraint user_logins_type_login_index unique (login, type)
);
