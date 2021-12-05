from marshmallow import Schema, fields as m_fields, utils, post_load
from datetime import datetime

DATETIME_FORMAT = 'iso'


class ArrayField(m_fields.Field):

    default_error_messages = {
        'required': 'Missing data for required field.',
        'null': 'Field may not be null.',
        'invalid': 'value must be array',
        'invalid_type': 'invalid data type',
        'enum': 'enum field -> unknown data'
    }

    def __init__(self, value, enum=None, *args, **kwargs):
        self.value = value
        self.enum = enum
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if not utils.is_iterable_but_not_string(value):
            self.fail('invalid')
        for item in value:
            if not isinstance(item, self.value):
                self.fail('invalid_type')
            if self.enum and item not in self.enum:
                self.fail('enum')
        return value

    def _deserialize(self, value, attr, data, **kwargs):
        if not utils.is_iterable_but_not_string(value):
            self.fail('invalid')
        for item in value:
            if not isinstance(item, self.value):
                self.fail('invalid_type')
            if self.enum and item not in self.enum:
                self.fail('enum')
        return value


class TripRequestSchema(Schema):
    transports = ArrayField(value=int, required=True)
    start_time = m_fields.DateTime(format=DATETIME_FORMAT, required=True)
    end_time = m_fields.DateTime(format=DATETIME_FORMAT, required=True)
    fields = ArrayField(value=str)
    group_by = ArrayField(value=str)


class ReportRequestSchema(Schema):
    id = m_fields.Integer(required=True)
    from_time = m_fields.DateTime(DATETIME_FORMAT, required=True)
    to_time = m_fields.DateTime(DATETIME_FORMAT, required=True)

    # @post_load
    # def validates_from_time(self, data: dict):
    #     data['from_time'] = data['from_time'].replace(tzinfo=None)
    #     data['to_time'] = data['to_time'].replace(tzinfo=None)
    #     return data
