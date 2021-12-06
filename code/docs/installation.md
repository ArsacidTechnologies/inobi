# Installation & Setup

## Prerequisites

Inobi server heavily depends following services:

- PostgresQL server (9.6 >=)
- Redis server

### PostgresQL

You will need to install postgres-server.
For Debian based distros you can install it with 
```bash
sudo apt install postgresql postgresql-10
```
After installation you will need to setup inobi database:
```bash
sudo -u postgres psql
# next lines put in psql prompt

# USERNAME and PASSWORD are placeholder for your credentials (ex.: username: inobi, password: "inobi") 
create user USERNAME with password "PASSWORD";

# DATABASENAME is name of database 
create database DATABASENAME with owner USERNAME;

# connect to inobi database in same psql shell
\c DATABASENAME

# create extension (note: double quotes here)
create extension "uuid-ossp";

```

### Redis

For Debian based distros installation:
```bash
sudo apt install redis-server
```

Make sure server is up
```bash
redis-cli ping
```
should output `PONG`. 

If redis server process didn't start automatically you can start it 
```bash
# using systemd cli
sudo systemctl start redis
sudo systemctl enable redis

# or just start it in separate terminal
redis-server /etc/redis/redis.conf
```

## Installation

First of all you'll need to clone latest code
```bash
git clone git@github.com:InobiLLC/inobi-backend.git
cd inobi-backend
```
Next commands will assume current working directory is at root of project.

### Configuration

Next you will need to prepare config file. For this, we use [`python-decouple`](https://github.com/henriquebastos/python-decouple) library. It uses variables from environment or config files. 
We can use .env or .ini files to configure Inobi server. Use example .ini file
```bash
cp settings.ini.example settings.ini
```
and edit `settings.ini` file, update PostgresQL and Redis server credentials. <br/>
***Note**: you may want to comment/delete Traccar configs for now to bootstrap integrations with traccar service later.*

### Dependencies

Create python environment using `virtualenv` or python's `venv` module. You may require to install them from and python-dev package to your system
```bash
sudo apt install python3-dev python3-venv
```
Now you can install python environment and dependencies in it.
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```




### Database schema setup

Inobi server does not create database, from now on app requires database is already created with uuid-ossp extension (see: PostgresQL installation section above).
Create database schema running command:
```bash 
# settings flask env vars

export FLASK_APP='inobi:make_app()'
export FLASK_DEBUG=1

PLEASE FIRST READ THE POSTGRES .TXT DOCS
AND THE LAST OF THIS PAGE FOR ID SEQUENCE
AND ANYTHING ELSE
flask db init
flask db migrate -m "MESSAGE"
# some legacy migration scripts
python ./run_old_migrations.py

# Sqlalchemy management 
flask db upgrade
```

### Server start

That's it, inobi ready to run.
```bash
python ./runserver.py --with-hooks
```

### Post configuration

#### Smart box

You may need to configure default Inobi Smart Box api response. Particularly the `version` of box's update and internet share permission. (see: inobi/transport/box/config.py)
```bash
# insert initial box version and internet values in db
sudo -u postgres psql
insert into box_settings (key, value) values ('transport:box:version', '1'), ('transport:box:internet', 'true');


# make sure resources directory are setup, they should be after runserver command
mkdir -p resources/transport/box/updates/

# create some empty update file that only saves version of box
cat > resources/transport/box/updates/update
version="$1"
VERSION_FILE='/version'

# remount read-only fs
sudo mount -o remount,rw /

# saving update version to version file 
echo "$version" | sudo tee "$VERSION_FILE"

sudo reboot
```

Now you can check that things are set up
```bash 
curl -s localhost:4325/transport/box/version | grep 1
curl -s localhost:4325/transport/box/internet | grep 1
curl -s localhost:4325/transport/box/update | md5sum - resources/transport/box/updates/update
```


#### Admin user

```bash
# temporarily add verified contact
sudo -u postgres psql
insert into verified_contacts (type, contact) values ('email', 'admin@gmail.com');

# note: password length must be more 6 chars
curl localhost:4325/app/v2/register -H 'Content-Type: application/json' -d '{"name": "Admin", "email": "admin@gmail.com", "username": "admin", "pwd": "admin123"}'

# add created user "inobi" (superuser) scope
# note: id in sql statement must be set from response of previous command
sudo -u postgres psql
update users set scopes = '["inobi"]' where id = 1;
```

We must add admin user in the `transport_admin` table of database too.

#### Transport Organization

```bash
sudo -u postgres psql

# insert some city info
insert into cities (name, lat, lng, zoom, lang, country, db_version, payload) values ('Qazvin', 36.2811997, 49.9466457, 12, 'fa', '{}', 1, '{}') returning id;

# insert organization info
# note: city_id is from previous response
insert into transport_organizations (name, traccar_username, traccar_password, payload, city, settings) values ('ARA', 'admin', 'admin', '{}', 1, '{}');

# insert organization admin
# note: user and organization ids
insert into transport_organization_users (organization, "user", role) values (1, 1, 'admin');
```

#### Traccar

```bash
-1- Install JDK 8 and JRE 8 with openjdk-8 and openjre-8
0- Create `traccar` database in Postgres and set user and password based on settings.ini
1- Install Traccar version 3.17 and not 4
1.5- Add these lines to /opt/traccar/conf/traccar.conf
    <entry key='database.driver'>org.postgresql.Driver</entry>
    <entry key='database.url'>jdbc:postgresql://127.0.0.1:5432/[DB]?sslmode=disable</entry>
    <entry key='database.user'>[USER]</entry>
    <entry key='database.password'>[PASS]</entry>
2- Run traccar service (linux and windows)
    sudo /opt/traccar/bin/startDaemon.sh
    sudo /opt/traccar/bin/stopDaemon.sh
3- Run traccar SQL commands for creation of tables manually.
4- They are stored in inobi/transport/traccar_md/sql/traccar_reports.sql
5- Change traccar password from 8082 port and set in settings.ini
```
For running two traccar on same machine, refer to https://www.traccar.org/forums/topic/two-servers-on-the-same-machine/
Could just change port in conf files and run a new instance with a new folder in /opt/

BTW, if server get down, we should restart traccar.
#### Redis

```bash
1- Install redis-server with apt-get
2- Change redis password in /etc/redis/redis.conf within `requirepass foobared` line
3- set redis password in settings.ini
```


Must install ffmpeg if want to upload video in inboi ads panel


Must change owner and permissions of resources folder for permission error while saving and uploading files.
Beacuse it may be in the root / directory.


Already, I couldn't find any way in each user apps (front, mobile)
that calls `city_database_upgrader` API. So after adding each route,
device, transport or city, We must call POST API of `/v1/cities/<city_id:int>/upgrader` manually.
For it's token, we should put this data in the payload of JWT
```js
  "user": {
    "id": 1
  },
  "transport_organization": {
    "id": 1,
    "city": {
      "id": 1
    }
  },
  "scopes": [
    "inobi"
  ]
```

We must first call `/v1/cities/<int:city_id>/upgrader/` to upgrade a city database.
Then call `/v1/cities/<int:city_id>/upgrader/<uuid:process_id>` to finish it's upgrade.
Then android app must call `city_data` API and then `subscribe`.

--------
After any changes to database models or their fields, must generate new migrations and run them again.
```
flask db migrate
flask db upgrade
```

Must set these functions owner to traccar user in postgres.
```
dump_transport_report
get_positions(timestamp with time zone, timestamp with time zone, int)
get_positions(timestamp with time zone, timestamp with time zone, int, float)
```

Must change ownership of ` inobi_device_dump` in postgres traccar

For changing the owner, plus specifying arguments datatype in parenthesis,
must connect to traccar user first, then set owner to traccar.

Must change timezone of postgres to the server timezone. As well as linux.
```SELECT * FROM pg_timezone_names;
alter database postgres SET timezone TO 'posix/Asia/Tehran';
alter database "db_inobi" set timezone to 'posix/Asia/Tehran';
SELECT pg_reload_conf();
```

You can set timezone param into pgsql/data/postgresql.conf file:
```timezone = 'posix/Asia/Tehran'```
and then restart postgresql sever.