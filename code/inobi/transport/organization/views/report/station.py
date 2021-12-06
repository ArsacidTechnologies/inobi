from inobi.transport.organization import bp
from inobi.transport.organization.serializers.reports import ReportRequestSchema
from inobi.security import secured
from inobi.utils.converter import converted
from flask_cors import cross_origin
from inobi import db
from inobi.utils import http_ok
import datetime
from inobi.security.scope import Transport
from inobi.transport.organization.utils import organization_required


@bp.route('/v1/reports/stations', methods=['GET'])
@cross_origin()
@secured(Transport.VIEWER)
@organization_required(is_table=False)
@converted(rest_key='rest')
def station_report(id: int, from_time: str, to_time: str, organization, rest=None):
    r_data = ReportRequestSchema().load({
        "id": id,
        "from_time": from_time,
        "to_time": to_time
    })
    sql = """select tt.id, u.name, t.name, t.device_id, r.type, r.name, tt.entry_time, tt.leave_time
                                from platform_time_travel tt
                                inner join transports t
                                    on tt.transport_id = t.id
                                inner join routes r
                                    on t.line_id = r.id
                                left join users u
                                    on u.id = t.driver
                                where t.id in (select transport from transport_organization_transports where organization = {}) and
                                tt.platform_id = {} and
                                    tt.time between '{}' and '{}'""".format(organization, r_data['id'],
                                                                            r_data['from_time'],
                                                                            r_data['to_time'])
    data = db.engine.execute(sql).fetchall()

    return http_ok({
        "data": [
            {
                "id": id,
                "driver": driver,
                "transport_name": transport_name if transport_name else transport_device,
                "route_type": route_type,
                "route_name": route_name,
                "entry_time": datetime.datetime.fromtimestamp(entry_time).isoformat(),
                "leave_time": datetime.datetime.fromtimestamp(leave_time).isoformat(),
                "duration": (leave_time - entry_time)
            }
            for id, driver, transport_name, transport_device, route_type, route_name, entry_time, leave_time in data
        ],
        "from_time": r_data['from_time'].isoformat(),
        "to_time": r_data['to_time'].isoformat()
    })
