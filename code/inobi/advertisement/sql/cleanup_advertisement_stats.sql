
do $$
declare DO_CLEANUP boolean = false;
begin
    if DO_CLEANUP then
        drop function if exists advertisement_daily_stats(float, float);
        drop function if exists advertisement_uniqueness_stats(float, float, int);
        drop function if exists advertisement_hourly_stats(float, float, int, int);
        drop function if exists advertisement_devices_stats(float, float);
    end if;
end;
$$;
