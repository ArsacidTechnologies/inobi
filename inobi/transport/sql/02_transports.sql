CREATE TABLE IF NOT EXISTS transports(
    id SERIAL PRIMARY KEY,
	device_id VARCHAR UNIQUE NOT NULL,
	line_id INT,
	device_phone VARCHAR NULL,
	name VARCHAR NULL,
	independent BOOLEAN DEFAULT TRUE,
	payload VARCHAR NULL,
	driver INT UNIQUE NULL,
	device_type VARCHAR NULL,
    ip VARCHAR NOT NULL,
    port SMALLINT NOT NULL,
    tts INT NOT NULL
);


CREATE TABLE IF NOT EXISTS transport_driver_changes(
    transport INT,
    "time" FLOAT,
    type VARCHAR,
    prev INT,
    "next" INT,
    reason VARCHAR,
    issuer INT
);


-- migrate driver int to driver unique int
do $$
begin
    if not exists(select constraint_name from information_schema.constraint_column_usage
        where constraint_name = 'transports_driver_key') then

        alter table transports drop driver;
        alter table transports add driver int unique null;
    end if;
end;
$$;


CREATE TABLE IF NOT EXISTS driver_transports(
    driver INT NOT NULL,
    transport INT NOT NULL
);
create unique index if not exists driver_transports_index on driver_transports(driver, transport);