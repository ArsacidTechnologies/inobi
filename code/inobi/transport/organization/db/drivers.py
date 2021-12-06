

import collections as C

from ...DataBase.classes import TransportOrganization, Transport

from inobi.mobile_app.db import user as user_db

import typing as T
from inobi import config
import psycopg2


from inobi.transport.DataBase.transport_v2 import delete_all_driver_transports
from inobi.transport.API.transport_v2 import unassign_driver_transport
from inobi.transport import error_codes
from .update_transport_drivers import update_driver_transport


Driver = user_db.User
DriverLogin = user_db.Login
DriverLoginTransport = T.Tuple[Driver, DriverLogin, T.Optional[Transport]]


class DriverLoginTransport(C.namedtuple('DriverLoginTransport', 'driver login transport')):

    def _asdict(self, **kwargs) -> dict:
        d = self.driver._asdict()
        d['login'] = self.login._asdict()

        d.update(kwargs)
        if self.transport:
            d['transport'] = self.transport._asdict()
        return d


def _make_driver_transport(row, login_index=len(Driver._fields), transport_index=len(Driver._fields)+len(DriverLogin._fields)) -> DriverLoginTransport:
    user = Driver.make(row, start_index=0)
    login = DriverLogin.make(row, start_index=login_index)

    try:
        transport = Transport.make_from_db_row(row, transport_index)
    except TypeError:
        transport = None

    return DriverLoginTransport(user, login, transport)


def drivers_of(torg_id: int, with_transport=False, driver_id: int = None) -> T.List[DriverLoginTransport]:

    with psycopg2.connect(config.SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:

            sql = '''
select u.*, l.*, {with_transport_select} from users u
    inner join transport_organization_drivers tod
        on tod.user = u.id
    inner join user_logins ul
        on u.id = ul."user"
    inner join logins l
        on ul.type = 'login' and ul.login = l.id
    left join transports t
        on t.driver = u.id
    where tod.organization = %s and {filter_clause}
'''.format(with_transport_select='t.*' if with_transport else '0',
           filter_clause='u.id = %s' if driver_id else '1 = 1')

            params = (torg_id, driver_id) if driver_id else (torg_id, )

            cursor.execute(sql, params)

            rows = list(cursor)

            return list(map(_make_driver_transport, rows))


def drivers_by_route(route_id: int) -> T.List[DriverLoginTransport]:

    with psycopg2.connect(config.SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            sql = '''
                select u.*, l.*, t.* from users u
                    inner join user_logins ul
                        on u.id = ul."user"
                    inner join logins l
                        on ul.type = 'login' and ul.login = l.id
                    inner join transports t
                        on t.driver = u.id
                    inner join routes r
                        on r.id = t.line_id
                where r.id = %s
            '''

            params = (route_id,)

            cursor.execute(sql, params)

            rows = list(cursor)

            return list(map(_make_driver_transport, rows))


def delete_driver_of(torg: TransportOrganization, driver_id: int) -> T.Optional[Driver]:
    with psycopg2.connect(config.SQL_CONNECTION) as conn:
        t = unassign_driver_transport(conn=conn, driver=driver_id, organization=torg.id)
        print(t)
        t = delete_all_driver_transports(conn=conn, driver=driver_id, organization=torg.id)
        print(t)
        with conn.cursor() as cursor:

            sql = '''
delete from users u 
    where u.id in (
        select "user" from transport_organization_drivers tod
            where tod.organization = %s
    )
    and u.id = %s
    returning *
'''
            cursor.execute(sql, (torg.id, driver_id))

            row = cursor.fetchone()
            if row is None:
                return None

            driver = Driver.make(row)

            sql = '''
do $$
declare torg_id int = %s;
declare user_id int = %s;
begin

    delete from logins 
        where id in (
            select login from user_logins
                where "user" = user_id
                    and type = 'login'
        );

    delete from social_users 
        where id in (
            select login from user_logins
                where "user" = user_id
                    and type = 'social_user'
        );

    delete from user_logins
        where "user" = user_id;

    delete from transport_organization_drivers
        where organization = torg_id and "user" = user_id;

end;
$$;
'''
            cursor.execute(sql, (torg.id, driver.id))
    return driver


OldDriver = Driver


def _update_driver(conn, id, torg_id, vals: dict) -> T.Optional[T.Tuple[Driver, OldDriver]]:
    with conn.cursor() as cursor:

        if len(vals) == 0:
            sql = '''
select u.*, u.* from users u
    inner join transport_organization_drivers tod
        on tod.user = u.id
    where u.id = %s and tod.organization = %s
'''
        else:
            sql = '''
update users u set
    {set_clause}
    from users as u2
        inner join transport_organization_drivers tod
            on tod.user = u2.id
    where u.id = %s and tod.organization = %s and u.id = u2.id
    returning u.*, u2.*
'''.format(set_clause=', '.join('{} = %s'.format(k) for k in vals))

        cursor.execute(sql, (*vals.values(), id, torg_id))

        row = cursor.fetchone()
        if row is None:
            return None
        updated = Driver.make(row)
        prev = Driver.make(row, start_index=len(Driver._fields))

        return updated, prev


OldDriverLogin = DriverLogin


def _update_driver_login(conn, driver_id, vals: dict) -> T.Optional[T.Tuple[DriverLogin, OldDriverLogin]]:
    with conn.cursor() as cursor:

        if len(vals) == 0:
            sql = '''
select l.*, l.* from logins l
    inner join user_logins ul on ul.login = l.id
    inner join users u on ul.user = u.id
    where u.id = %s
'''
        else:
            sql = '''
update logins l set
    {set_clause}
    from logins as l2
        inner join user_logins ul on ul.login = l2.id
        inner join users u on ul.user = u.id
    where u.id = %s and l.id = l2.id
    returning l.*, l2.*
'''.format(set_clause=', '.join('{} = %s'.format(k) for k in vals))

        cursor.execute(sql, (*vals.values(), driver_id))

        row = cursor.fetchone()
        if row is None:
            return None
        updated = DriverLogin.make(row)
        prev = DriverLogin.make(row, start_index=len(DriverLogin._fields))

        return updated, prev


def update_driver_of(torg: TransportOrganization, driver: Driver, login: DriverLogin, tr_stuff: dict) -> T.Optional[T.Tuple[Driver, Driver, DriverLogin, DriverLogin]]:

    drivers_vals = driver.update_values()
    drivers_login_vals = login.update_values()

    driver_id = drivers_vals.pop('id')

    if len(drivers_vals) + len(drivers_login_vals) + len(tr_stuff) == 0:
        raise user_db.InobiException('No Values To Update',
                                     error_codes.NO_VALUES_TO_UPDATE)

    with psycopg2.connect(config.SQL_CONNECTION) as conn:
        r = _update_driver(conn, driver_id, torg.id, drivers_vals)
        if r is None:
            return None
        driver, prev_d = r

        r = _update_driver_login(conn, driver_id, drivers_login_vals)
        if r is None:
            return None
        login, prev_login = r
        if tr_stuff:
            update_driver_transport(conn=conn, tr_stuff=tr_stuff, driver=driver.id, organization=torg.id)

        return driver, prev_d, login, prev_login

