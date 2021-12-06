from inobi.transport.DataBase.transport_v2 import get_all_transports
from inobi.transport.DataBase.line_v2 import get_lines, get_all_lines, get_all_directions
from inobi.transport.organization.db.organization import get_organizations
from inobi.transport.traccar_md.requests import get_users, save_user, get_groups, \
    save_group, get_geofences, save_geofence, save_permission, get_devices, save_device, \
    update_device, update_geofences, delete_permissions
from inobi.transport.traccar_md.db import get_group_by_line, get_user_by_organization, \
    get_geofence_by_direction, init_db
from inobi.config import SQL_CONNECTION
import psycopg2
import sqlite3
from inobi.transport.configs import traccar_dbpath
from inobi.utils import timeit
from inobi.transport.configs import traccar_region, traccar_colors
from inobi.transport.exceptions import TransportException
from ..traccar_md import logger


def sync_direction_geofence(conn, lite_conn, force=False):
    geofences = get_geofences()
    directions = get_all_directions(conn)
    direction_geofence = set()
    for (direction, line) in directions:
        dfound = False
        for geofence in geofences:
            if geofence['id'] == 0:
                continue
            if '{}/{}/{}'.format(line.type, line.name, direction.type) == geofence['name']:
                if traccar_region == geofence['attributes'].get('region'):
                    direction_geofence.add((direction.id, geofence['id']))
                    if force:
                        logger.info('UPDATE GEO {}'.format(geofence['name']))
                        update_geofences(id=geofence['id'],
                                         name=geofence['name'],
                                         area=direction.line,
                                         description=direction.type,
                                         attrs=dict(region=traccar_region,
                                                    color=traccar_colors.get(direction.type, '')))
                    dfound = True
                    break
        if not dfound:
            logger.info("SAVING GEO {}".format('{}/{}/{}'.format(line.type, line.name, direction.type)))
            geofence = save_geofence(name='{}/{}/{}'.format(line.type, line.name, direction.type),
                                     area=direction.line,
                                     description=direction.type,
                                     attrs=dict(region=traccar_region,
                                                color=traccar_colors.get(direction.type, '')))
            direction_geofence.add((direction.id, geofence['id']))
            group_id = get_group_by_line(lite_conn, line.id)
            logger.info("SAVING permissions group_id={} geofence_id={}".format(group_id, geofence['id']))
            save_permission(url='/groups/geofences', group_id=group_id, geofence_id=geofence['id'])
    cursor = lite_conn.cursor()
    cursor.executemany('insert into direction_geofence values (?, ?)', list(direction_geofence))


def sync_line_group(conn, lite_conn):
    lines = get_all_lines(conn)
    groups = get_groups()
    net = []
    for line in lines:
        found = False
        for group in groups:
            if '{}/{}'.format(line.type, line.name) == group['name']:
                if traccar_region == group['attributes'].get('region'):
                    net.append((line.id, group['id']))
                    found = True
                    break
        if not found:
            logger.info('SAVING GROUP {}'.format('{}/{}'.format(line.type, line.name)))
            group = save_group(name='{}/{}'.format(line.type, line.name),
                               attrs=dict(
                                   from_name=line.from_name,
                                   to_name=line.to_name,
                                   type=line.type,
                                   region=traccar_region
                               ))
            net.append((line.id, group['id']))
    cursor = lite_conn.cursor()
    cursor.executemany('insert into line_group values (?, ?)', net)


def sync_transport_device(transports):
    devices = get_devices() or []
    net = []

    for transport in transports:
        if transport.device_id not in devices:
            logger.info('SAVING TRANSPORT {}'.format(transport.device_id))
            device = save_device(
                name=transport.name or transport.device_id,
                unique_id=transport.device_id,
            )
    return
    #     found = False
    #     for device in devices:
    #         if transport.device_id == device['uniqueId']:
    #             group_id = get_group_by_line(lite_conn, transport.line_id)
    #             if (group_id != device['groupId']) or \
    #                     ((transport.name or transport.device_id) != device['name']) or \
    #                     ((transport.device_phone if transport.device_phone else None) != device.get('phone')):
    #                 logger.info('UPDATE DEVICE {}'.format(transport.device_id))
    #                 if transport.payload:
    #                     attrs = transport.payload
    #                     attrs.update(dict(region=traccar_region))
    #                 else:
    #                     attrs = dict(region=traccar_region)
    #                 update_device(id=device['id'],
    #                               unique_id=transport.device_id,
    #                               name=transport.name or transport.device_id,
    #                               group_id=group_id,
    #                               phone=transport.device_phone,
    #                               attrs=attrs)
    #
    #             net.append((transport.id, device['id']))
    #             found = True
    #             break
    #     if not found:
    #         logger.info('SAVING TRANSPORT {}'.format(transport.device_id))
    #         group_id = get_group_by_line(lite_conn, transport.line_id)
    #         if transport.payload:
    #             transport.payload.update(dict(region=traccar_region))
    #             attrs = transport.payload
    #         else:
    #             attrs = dict(region=traccar_region)
    #         device = save_device(
    #             name=transport.name or transport.device_id,
    #             unique_id=transport.device_id,
    #             group_id=group_id,
    #             phone=transport.device_phone,
    #             attrs=attrs
    #         )
    #         net.append((transport.id, device['id']))
    # cursor = lite_conn.cursor()
    # cursor.executemany('insert into transport_device values (?, ?)', net)


def sync_organization_user(lite_conn, organizations):
    users = get_users()
    net = set()
    for organization in organizations:
        if not organization.traccar_password or not organization.traccar_username:
            raise TransportException("organization's traccar credentials not set", 400)
        found = False
        for user in users:
            if organization.traccar_username == user['email']:
                net.add((organization.id, user['id']))
                found = True
                break
        if not found:
            logger.info("SAVING USER {}".format(organization.traccar_username))
            user = save_user(organization.traccar_username, organization.traccar_password, attrs=dict(region=traccar_region))
            net.add((organization.id, user['id']))

    cursor = lite_conn.cursor()
    cursor.executemany('insert into organization_user values (?, ?)', net)


def link_all_things(conn, lite_conn, organizations):
    for organization in organizations:
        user_id = get_user_by_organization(lite_conn, organization.id)

        lines = get_lines(conn=conn, organization_id=organization.id)
        groups = get_groups(user_id)
        _lines = set([get_group_by_line(lite_conn, line.id) for line in lines])
        _groups = set([group['id'] for group in groups])
        to_save_groups = _lines.difference(_groups)
        to_del_groups = _groups.difference(_lines)

        for group in to_save_groups:
            logger.info('SAVE /permissions user_id={} group_id={}'.format(user_id, group))
            save_permission('/permissions', user_id=user_id, group_id=group)
            # save_permission('/permissions', user_id=user_id, group_id=group)
        for group in to_del_groups:
            logger.info('DELETE /permissions user_id={} group_id={}'.format(user_id, group))
            delete_permissions('/permissions', user_id=user_id, group_id=group)
            # delete_permissions('/permissions', user_id=user_id, group_id=group)

        _lines.update(_groups)
        _lines.difference_update(to_del_groups)

        directions = get_all_directions(conn, organization.id)
        geofences = get_geofences(user_id=user_id)
        _directions = set([get_geofence_by_direction(lite_conn, direction.id) for direction, line in directions])
        _geofences = set([geofence['id'] for geofence in geofences])
        to_save_geo = _directions.difference(_geofences)
        to_del_geo = _geofences.difference(_directions)
        for geo in to_save_geo:
            logger.info('SAVE /permissions/geofences user_id={} geofence_id={}'.format(user_id, geo))
            save_permission(url='/permissions/geofences', user_id=user_id, geofence_id=geo)
        for geo in to_del_geo:
            logger.info('DELETE /permissions/geofences user_id={} geofence_id={}'.format(user_id, geo))
            delete_permissions(url='/permissions/geofences', user_id=user_id, geofence_id=geo)


@timeit
def sync_traccar_md(force_update_line=False):
    with psycopg2.connect(SQL_CONNECTION) as conn:
        # with sqlite3.connect(traccar_dbpath) as lite_conn:
            # init_db(lite_conn)

            # organizations = get_organizations(conn)
            transports = get_all_transports(conn)

            # sync_line_group(conn, lite_conn)
            # lite_conn.commit()
            # sync_direction_geofence(conn, lite_conn, force_update_line)
            sync_transport_device(transports)
            # sync_organization_user(lite_conn, organizations)

            # link_all_things(conn, lite_conn, organizations)
