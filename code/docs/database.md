List of ID sequences

    transport_organizations_id_seq
    transport_organization_notifications_id_seq
    transports_id_seq
    users_id_seq
    social_users_id_seq
    logins_id_seq
    verified_contacts_id_seq
    cities_id_seq
    messages_id_seq
    advertisement_users_id_seq
    advertisement_user_devices_id_seq
    advertisement_user_logins_id_seq
    chronicles_id_seq
    eta_passes_time_id_seq
    user_logins_id_seq
    platform_time_travel_id_seq
    stations_id_seq
    routes_id_seq
    transport_organization_audio_info_id_seq
    platforms_id_seq
    exclude_routes_id_seq
    directions_id_seq
    audio_info_file_id_seq
    direction_platforms_id_seq
    breakpoints_id_seq
    station_routes_id_seq
    station_platforms_id_seq
    route_directions_id_seq
    transport_organization_users_id_seq
    advertisement_groups_id_seq
    advertisement_devices_id_seq
    advertisement_viewers_id_seq
    advertisement_views_id_seq

-----------

Backup from a table in one database to a table in another database

    pg_dump -a -t route_directions old_inobi | psql inobi-db
