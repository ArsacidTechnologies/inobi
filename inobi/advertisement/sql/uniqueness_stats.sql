
create or replace function advertisement_uniqueness_stats(start_ts float, end_ts float, group_views_upper_to int = 5)
    returns table (num_of_views bigint, users_count int, views_of_all_ratio float, users_of_all_ratio float) as $$
declare
    total_views float;
    total_users float;
begin
    
    total_views = count(*) from chronicles where time between start_ts and end_ts;
    total_users = count(q.*) from (select client_mac from chronicles where time between start_ts and end_ts group by client_mac) q;

    return query 
    select g, cast(sum(uc) as int), cast(sum(c*uc) as float)/total_views, cast(sum(uc) as float)/total_users from (
        select c, count(c) as uc, (case when c < group_views_upper_to then c else group_views_upper_to end) as g from (
            select count(client_mac) as c from chronicles
                where time between start_ts and end_ts 
                    and client_mac != '<incomplete>'
                group by client_mac
        ) q1
            group by q1.c
            order by q1.c
    ) q2
        group by g
        order by g;
end;
$$ language plpgsql;


-- select * from advertisement_uniqueness_stats(1495602273.0, 1521786457.0);
