

create table if not exists verified_contacts (
    id serial primary key,
    time float not null default extract(epoch from now()),
    contact varchar unique not null,
    type varchar not null
--    constraint verified_contacts_contact_type_index unique (contact, type)
);
