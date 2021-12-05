from inobi.transport.organization import bp
from flask_cors import cross_origin
from inobi.security import secured
from inobi.utils.converter import converted
from inobi.transport.organization.serializers.reports import ReportRequestSchema
from inobi import db
from inobi.transport.organization.utils import organization_required
from inobi.transport.DataBase.models import Transport, Station, Platform, PlatformTimeTravel as PTT, Route, Direction
from inobi.transport.organization.db.models import TransportOrganization as TO
from inobi.utils import http_ok
from sqlalchemy import func
from sqlalchemy.sql.expression import label
from inobi.security.scope import Transport as Scope


@bp.route('/v1/reports/transports/stations', methods=['GET'])
@cross_origin()
@secured(Scope.VIEWER)
@organization_required(is_table=False)
@converted(rest_key='rest')
def transport_station_report(id: int, from_time: str, to_time: str, organization: int, rest=None):
    r_data = ReportRequestSchema().load({
        "id": id,
        "from_time": from_time,
        "to_time": to_time
    })
    id, from_time, to_time = r_data['id'], r_data['from_time'], r_data['to_time']

    from_time, to_time = sorted([from_time, to_time])

    q = db.session.query(
                        Station.id.label('station_id'),
                        Station.name.label('station_name'),
                        PTT.leave_time,
                        PTT.entry_time,
                        label('duration', PTT.leave_time - PTT.entry_time),
                        func.extract('epoch', PTT.time).label('register_time'))\
        .join(Transport, TO.transports)\
        .join(PTT, PTT.transport_id == Transport.id)\
        .join(Platform, PTT.platform_id == Platform.id)\
        .join(Station, Platform.stations)\
        .filter(Transport.id == id, TO.id == organization, PTT.time.between(from_time, to_time))\
        .order_by(PTT.time)\
        .all()

    resp = list(map(lambda x: x._asdict(), q))
    return http_ok({"data": resp})


