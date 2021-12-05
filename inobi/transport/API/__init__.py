from inobi import add_prerun_hook
from .redis_v2 import delete, sync
import logging
logger = logging.getLogger(__name__)
from ..configs import TKeys


def clear_redis():
    pass
    # params = [TKeys.TRANSPORTS, TKeys.ORGANIZATION_LINES, TKeys.UNKNOWNS, TKeys.LINES, TKeys.ORGANIZATIONS]
    # ok = delete(params)
    # logger.info("REDIS CLEANED {}".format(ok))

    # params = ['buses', 'lines', 'unknown']
    # ok = delete(params, segment=RedisSegments.BUSES)
    # logger.info("REDIS V1 CLEANED {}".format(ok))


add_prerun_hook(sync)
