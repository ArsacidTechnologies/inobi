create table if not exists transport_report(
    id serial primary key,
    day date,
    deviceid int,
    average_speed float,
    max_speed float,
    passengers_in int,
    passengers_out int,
    distance float,
    payload json
);
create table if not exists inobi_device_dump(
  id serial primary key,
  day date,
  device_id int,
  out_of_route json,
  trips json,
  stops json
);

create unique index if not exists transport_report_day on transport_report(day, deviceid);

create or replace function dump_transport_report(d date)
returns void AS $$
    BEGIN   
    insert into transport_report (day, deviceid, average_speed, max_speed, passengers_in, passengers_out, distance)
        select 
            d,
            deviceid as device_id,
            (avg(speed) * 1.852) as average_speed, 
            (max(speed) * 1.852) as max_speed, 
            coalesce(sum((attrs->>'passengers_in')::float::int), 0) as passengers_in,
            coalesce(sum((attrs->>'passengers_out')::float::int), 0) as passengers_out,
            sum((attrs->>'distance')::float)/1000 as distance
        from (
            select
                case
                    when speed > 54 then null
                    when speed < 54 then speed
                end as speed,
                deviceid, 
                fixtime, 
                attributes::json as attrs 
            from positions 
            where 
                fixtime between d::timestamp and d + '23:59:59'::time
        ) q group by deviceid
    on conflict(day, deviceid) do update set 
        average_speed = excluded.average_speed, 
        max_speed = excluded.max_speed, 
        passengers_out = excluded.passengers_out,
        passengers_in = excluded.passengers_in,
        distance = excluded.distance;
    END;
$$ LANGUAGE plpgsql;


--DROP FUNCTION get_positions (entry timestamp, leave timestamp, boxid int, altitude_filter float);
--DROP FUNCTION get_positions (entry timestamp, leave timestamp, boxid int);


CREATE OR REPLACE FUNCTION get_positions (entry timestamp with time zone, leave timestamp with time zone, boxid int)
    RETURNS TABLE (
     fixtime timestamp with time zone,
     latitude FLOAT,
     longitude FLOAT,
     attributes VARCHAR,
     speed FLOAT,
     altitude FLOAT
    )
    AS $$
    BEGIN
        RETURN QUERY
        select
            p.fixtime::timestamp with time zone,
            p.latitude,
            p.longitude,
            p.attributes,
            p.speed,
            p.altitude
        from positions as p
        where
            p.deviceid = boxid and
            p.fixtime between entry and leave
        order by p.fixtime;
    END; $$
    LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION get_positions (entry timestamp with time zone, leave timestamp with time zone, boxid int, altitude_filter float)
    RETURNS TABLE (
     fixtime timestamp with time zone,
     latitude FLOAT,
     longitude FLOAT,
     attributes VARCHAR,
     speed FLOAT,
     altitude FLOAT
    )
    AS $$
    BEGIN
        RETURN QUERY
        select
            p.fixtime::timestamp with time zone,
            p.latitude,
            p.longitude,
            p.attributes,
            p.speed,
            p.altitude
        from positions as p
        where
            p.deviceid = boxid and
            p.fixtime between entry and leave and
            p.altitude = altitude_filter
        order by p.fixtime;
    END; $$
    LANGUAGE 'plpgsql';


