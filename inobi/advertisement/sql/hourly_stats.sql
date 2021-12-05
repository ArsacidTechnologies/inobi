
create or replace function advertisement_hourly_stats(start_ts float, end_ts float, group_lower_to int = 6, group_upper_to int = 21)
    returns table (hour int, views float, views_total int) as $$
begin

    return query select cast(h as int), count(*)/((end_ts-start_ts)/60.0/60.0/24.0) as avg_views, cast(count(*) as int) as total from (
        select (case when h <= group_lower_to then group_lower_to when h >= group_upper_to then group_upper_to else h end) as h from (
            select  
                extract(hour from to_timestamp(time)) as h
            from chronicles
                where /*
                    client_mac is not null
                    and client_mac != '<incomplete>'
                    and */time between start_ts and end_ts
        ) _ii
    ) _i
        group by h
        order by cast(h as int);
end;
$$ language plpgsql;

-- select * from advertisement_hourly_stats(1495602273.0, 1521786457.0);
