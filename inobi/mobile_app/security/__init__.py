from functools import partial

from .facebook import verify as _verify_facebook, ID_KEY as _FACEBOOK_ID_KEY
from .google import verify as _verify_google, ID_KEY as _GOOGLE_ID_KEY
from .app import verify, ID_KEY as _INOBI_ID_KEY

from .app import check_with_abort


LOGIN_HANDLERS = {
    'facebook': _verify_facebook,
    'google': _verify_google,
    'update': partial(verify, base64=True)
}

ENTRY_POINT_LOGINS = set(k for k in LOGIN_HANDLERS.keys() if k not in ('update', ))

ID_KEYS = {
    'facebook': _FACEBOOK_ID_KEY,
    'google': _GOOGLE_ID_KEY,
    'update': _INOBI_ID_KEY
}
