CREATE TABLE IF NOT EXISTS stations(
    id SERIAL PRIMARY KEY,
    name varchar,
    full_name varchar);

CREATE TABLE IF NOT EXISTS routes(
    id SERIAL PRIMARY KEY,
    type varchar,
    name varchar,
    from_name varchar,
    to_name varchar);

CREATE TABLE IF NOT EXISTS directions(
    id SERIAL PRIMARY KEY,
    type varchar,
    line varchar);

CREATE TABLE IF NOT EXISTS platforms(
    id SERIAL PRIMARY KEY,
    lat REAL,
    lng REAL);

CREATE TABLE IF NOT EXISTS station_platforms(
    id INT,
    pos INT,
    entry_id INT);

CREATE TABLE IF NOT EXISTS station_routes(
    id INT,
    pos INT,
    entry_id INT);

CREATE TABLE IF NOT EXISTS route_directions(
    id INT,
    pos INT,
    entry_id INT);

CREATE TABLE IF NOT EXISTS direction_platforms(
    id INT,
    pos INT,
    entry_id INT);

create table IF NOT EXISTS exclude_routes(
    route_id INT PRIMARY KEY
);

create table if not exists breakpoints(
    id int,
    entry_id int
);

CREATE TABLE if not exists direction_links (
    dfrom int,
    dto int,
    type int,
    pfrom int,
    pfromi int,
    pto int,
    ptoi int,
    primary key(dfrom, dto, type)
);


