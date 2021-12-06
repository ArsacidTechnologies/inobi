








CREATE extension "uuid-ossp";
CREATE USER traccar with PASSWORD 'traccar';
CREATE DATABASE traccar WITH OWNER traccar;
GRANT ALL PRIVILEGES ON DATABASE inobi TO inobi;
GRANT ALL PRIVILEGES ON DATABASE traccar TO traccar;
ALTER ROLE inobi superuser;
ALTER ROLE traccar superuser;
-- ALTER DATABASE postgres SET timezone='posix/Asia/Tehran';
-- ALTER DATABASE inobi SET timezone='posix/Asia/Tehran';
