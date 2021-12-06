delete from transport_organization_lines
where line not in (select id from routes);

insert into transport_organization_directions (organization, direction)
select 1, id from directions;

insert into transport_organization_platforms (organization, platform)
select 1, id from platforms;

insert into transport_organization_stations (organization, station)
select 1, id from stations;



DO $$
    declare max_i int;
    begin
        max_i = max(id) + 1 from platforms;
        raise notice '%', max_i;
        execute format('alter sequence platforms_id_seq restart with %s', max_i);
    end;
$$;

DO $$
    declare max_i int;
    begin
        max_i = max(id) + 1 from routes;
        raise notice '%', max_i;
        execute format('alter sequence routes_id_seq restart with %s', max_i);
    end;
$$;
DO $$
    declare max_i int;
    begin
        max_i = max(id) + 1 from directions;
        raise notice '%', max_i;
        execute format('alter sequence directions_id_seq restart with %s', max_i);
    end;
$$;
DO $$
    declare max_i int;
    begin
        max_i = max(id) + 1 from stations;
        raise notice '%', max_i;
        execute format('alter sequence stations_id_seq restart with %s', max_i);
    end;
$$;
