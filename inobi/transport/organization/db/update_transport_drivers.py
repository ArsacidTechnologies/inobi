from inobi.transport.DataBase.transport_v2 import delete_driver_transports, \
    save_driver_transports
from inobi.transport.API.transport_v2 import unassign_driver_transport, update_driver_transports as udt
from inobi.redis import getredis
from inobi.config import RedisSegments
from inobi.utils import connected
from inobi.transport.exceptions import TransportException
from inobi.transport import error_codes


@connected
def update_driver_transport(*, conn, tr_stuff: dict, driver: int, organization: int, redis=None):
        for required in ['transport', 'available_transport']:
            if required not in tr_stuff:
                raise TransportException('transport and available_transport required',
                                         error_codes.TRANSPORT_AND_AVAILABLE_TRANSPORT_REQUIRED)
        if not isinstance(tr_stuff['available_transport'], list):
            raise TransportException('available_transport must be list of int',
                                     error_codes.AVAILABLE_TRANSPORT_MUST_BE_LIST_OF_INT)
        for item in tr_stuff['available_transport']:
            if not isinstance(item, int):
                raise TransportException('available_transport must be list of int',
                                         error_codes.AVAILABLE_TRANSPORT_MUST_BE_LIST_OF_INT)
        if tr_stuff.get('transport'):
            if not isinstance(tr_stuff['transport'], int):
                raise TransportException('transport must be int',
                                         error_codes.TRANSPORT_MUST_BE_INT)
            if tr_stuff['transport'] not in tr_stuff['available_transport']:
                raise TransportException('transport must be in available_transport',
                                         error_codes.TRANSPORT_MUST_BE_IN_AVAILABLE_TRANSPORT)

        if tr_stuff['available_transport']:
            delete_driver_transports(conn=conn, driver=driver, organization=organization)
            save_driver_transports(conn=conn, driver=driver, transports=tr_stuff['available_transport'],
                                   organization=organization)
        else:
            delete_driver_transports(conn=conn, driver=driver, organization=organization)
        if not redis:
            redis = getredis(RedisSegments.BUSES_V2)
        if tr_stuff['transport']:
            unassign_driver_transport(conn=conn, driver=driver, organization=organization, redis=redis)
            udt(conn=conn, driver=driver, transport=tr_stuff['transport'],
                organization=organization, redis=redis)
        else:
            unassign_driver_transport(conn=conn, driver=driver, organization=organization, redis=redis)