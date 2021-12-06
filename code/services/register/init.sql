






insert into verified_contacts (type, contact) values ('email', 'admin@gmail.com');
update users set scopes = '["inobi"]' where id = 1;
insert into box_settings (key, value) values ('transport:box:version', '1'), ('transport:box:internet', 'true');
insert into cities (name, lat, lng, zoom, lang, country, db_version, payload) values ('Tehran', 35.6892, 51.3890, 12, 'fa', '{}', 1, '{}') returning id;
insert into transport_organizations (name, traccar_username, traccar_password, payload, city, settings) values ('ARA', 'admin', 'admin', '{}', 1, '{}');
insert into transport_organization_users (organization, "user", role) values (1, 1, 'admin');
insert into transport_organization_admins (organization, "user") values (1, 1);