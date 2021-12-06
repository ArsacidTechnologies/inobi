
do $$
begin
    if not exists(select 1 from pg_type where typname = 'advertisement_devices_stats_result') then
        create type advertisement_devices_stats_result as (
            total int, 
            android int, android_ratio float, 
            ios int, ios_ratio float, 
            unknown int, unknown_ratio float
        );
    end if;
end;
$$;

create or replace function advertisement_devices_stats(start_ts float, end_ts float)
    returns advertisement_devices_stats_result as $$
declare 
    total int;
    android float;
    ios float;
    unknown float;
begin
    total = count(*) from chronicles
        where time between start_ts and end_ts;

    android = count(*) from chronicles
        where time between start_ts and end_ts
            and device ilike '%android%';

    ios = count(*) from chronicles
        where time between start_ts and end_ts
            and (device ilike '%iphone%' or device ilike '%ipad%');

    unknown = total-android-ios;

    return (total, cast(android as int), android/total, cast(ios as int), ios/total, cast(unknown as int), unknown/total);
end;
$$ language plpgsql;


-- select * from advertisement_devices_stats(1495602273.0, 1521786457.0);
