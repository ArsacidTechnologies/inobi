
import typing as T
from inobi import db
from inobi.utils import AsDictMixin, LocatedMixin, UpdateMixin

from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime
import time

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship, foreign, remote

from .models import Device, Group


def _query(model, **filter_kwargs):
    return db.session.query(model).filter_by(**filter_kwargs)


def find_device(**kwargs) -> T.Optional[Device]:
    return _query(Device, **kwargs).first()


def fetch_device(id):
    return db.session.query(Device).get(id)


def fetch_devices(groups=False, id=None) -> T.List[Device]:
    if id is not None:
        return fetch_device(id)

    q = db.session.query(Device)
    if not groups:
        q = q.filter(Device.group_id.is_(None))
    else:
        q = q.filter(Device.group_id.isnot(None))
    return q.all()


def create_device(device_id: str,
                  name: str = None, description: str = None,
                  enabled: bool = True, group_id: int = None,
                  city_id: int = None, location: dict = None,
                  ) -> Device:

    d = Device(device_id=device_id, name=name, description=description,
               enabled=enabled, group_id=group_id,
               city_id=city_id, location=location)
    db.session.add(d)
    db.session.commit()
    return d


def delete_device(device: Device):
    db.session.delete(device)
    db.session.commit()
    return device


def update_device(device: Device, values: dict):
    device.update(values, updated=datetime.utcnow())
    db.Session.object_session(device).commit()


def create_group(name: str,
                 description: str = None, enabled: bool = True,
                 parent_group_id: int = None,
                 location: dict = None,
                 city_id: int = None
                 ) -> Group:

    g = Group(name=name, description=description, enabled=enabled, parent_group_id=parent_group_id,
              city_id=city_id, location=location)
    db.session.add(g)
    db.session.commit()
    return g


def fetch_group(id):
    return db.session.query(Group).get(id)


def fetch_groups(groups=False, id=None) -> T.List[Group]:
    if id is not None:
        return fetch_group(id)

    q = db.session.query(Group)\
        .options(db.joinedload(Group.devices))\
        .options(db.joinedload(Group.groups))

    if not groups:
        q = q.filter(Group.parent_group_id.is_(None))
    else:
        q = q.filter(Group.parent_group_id.isnot(None))

    return q.all()


def delete_group(group: Group):
    db.session.delete(group)
    db.session.commit()
    return group


def update_group(group: Group, values: dict):
    group.update(values, updated=datetime.utcnow())
    db.Session.object_session(group).commit()


fetch = fetch_devices
create = create_device
delete = Device.delete = delete_device
update = update_device

Group.delete = delete_group
