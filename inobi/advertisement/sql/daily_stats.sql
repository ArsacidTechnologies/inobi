
create or replace function advertisement_daily_stats(start_ts float, end_ts float)
    returns table (views int, dt date) as $$
begin
    return query select cast(count(*) as int), q1.dt from (
            select to_timestamp(time)::date as dt from chronicles
                where time between start_ts and end_ts
        ) q1
            group by q1.dt
            order by q1.dt;
end;
$$ language plpgsql;


-- select * from advertisement_daily_stats(1495602273.0, 1521786457.0);
