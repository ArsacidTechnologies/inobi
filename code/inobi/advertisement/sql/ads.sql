

CREATE TABLE IF NOT EXISTS ads (
	id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
	type varchar(20) NOT NULL,
	duration float NOT NULL,
	redirect_url varchar NOT NULL,
	weight int NOT NULL DEFAULT 1,
	views int NOT NULL DEFAULT 0,
	source varchar NOT NULL,
	created float NOT NULL,
	enabled boolean NOT NULL default true,
	title varchar NOT NULL,
	description varchar NULL,
	lat float NULL,
	lng float NULL,
	views_max int NULL,
	expiration_date float NULL,
	requests int NOT NULL DEFAULT 0,
	platform int not null default 1023,
	radius float not null default 0.5,
	transport_filters varchar[] default null,
    cities int[] null,
    time_from time null,
    time_to time null,
    start_date float null
);

-- added transport_filters column
do $$
begin
    if not exists(select 1 from information_schema.columns
        where column_name = 'transport_filters' and table_name = 'ads' ) then
        raise notice 'kek';
        alter table ads add column transport_filters varchar[] default null;
    end if;
end;
$$;


-- add cities, time_from, time_to columns
do $$
begin
    if not exists(select 1 from information_schema.columns
        where column_name in ('cities', 'time_from', 'time_to') and table_name = 'ads' ) then
        raise notice 'kek';
        alter table ads add column cities int[] null;
        alter table ads add column time_from time null;
        alter table ads add column time_to time null;
    end if;
end;
$$;



-- added start_date column
do $$
begin
    if not exists(select 1 from information_schema.columns
        where column_name in ('start_date') and table_name = 'ads' ) then
        raise notice 'kek';
        alter table ads add column start_date float null;
    end if;
end;
$$;

