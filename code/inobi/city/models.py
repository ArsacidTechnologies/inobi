

from inobi import db

from inobi.utils import AsDictMixin

import json


class City(db.Model, AsDictMixin):

    _asdict_fields = 'id name lat lng zoom lang country db_version _payload:payload'.split()

    __tablename__ = 'cities'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String, nullable=False)

    lat = db.Column(db.Float(precision=15), nullable=False)
    lng = db.Column(db.Float(precision=15), nullable=False)

    zoom = db.Column(db.Float(precision=15), default='12.0', server_default='12.0', nullable=False)

    lang = db.Column(db.String, nullable=False, default='en', server_default='en')

    country = db.Column(db.String, nullable=True)

    db_version = db.Column(db.Integer, default='1', nullable=False, server_default='1')

    payload = db.Column(db.String, nullable=True, default='{}', server_default='{}')

    @property
    def _payload(self):
        if self.payload:
            return json.dumps(self.payload)
