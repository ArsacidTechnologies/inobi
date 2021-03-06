

# Transport Middle Ware
TRACCAR_SYNC_REQUIRED = 100


LINE_NOT_FOUND = 101
ACCESS_DENIED = 102
DRIVER_DOES_NOT_HAVE_TRANSPORT = 103
TRANSPORT_NOT_FOUND = 104
TRANSPORT_DEVICE_ID_MUST_BE_UNIQUE = 105
DRIVER_ALREADY_HAS_A_TRANSPORT = 106
JSON_REQUIRED = 107
ID_MUST_BE_DIGIT = 108
MISSING_ID = 109
PAYLOAD_MUST_BE_DICTIONARY = 110
DRIVER_MUST_BE_DIGIT = 111
START_DATE_MUST_BE_DIGIT = 112
END_DATE_MUST_BE_DIGIT = 113
TYPE_NOT_FOUND = 114
INVALID_PICTURE = 115

EMPTY_DEVICE_ID_PARAMETER = 116
EMPTY_LINE_ID_PARAMETER = 117
EMPTY_DEVICE_PHONE_PARAMETER = 118
EMPTY_NAME_PARAMETER = 119
EMPTY_IP_PARAMETER = 120
EMPTY_PORT_PARAMETER = 121
EMPTY_TTS_PARAMETER = 122


DEVICE_ID_MUST_BE_STRING = 120
LINE_ID_MUST_BE_INT = 121


PLATFORM_NOT_FOUND = 122
STATION_NOT_FOUND = 123
DIRECTION_NOT_FOUND = 124
ROUTE_NOT_FOUND = 125
INCORRECT_DIRECTION_TYPE = 126
INCORRECT_ROUTE_TYPE = 127
NAME_MUST_BE_DIGIT = 128
FILE_REQUIRED = 129
LANG_NOT_FOUND = 130
FILE_MUST_BE_WAV = 131
_2_DIR_REQUIRED = 132
INCORRECT_PLATFORM_STRUCTURE = 133
PLATFORM_ALREADY_HAS_A_STATION = 134
DIRECTION_ALREADY_HAS_A_ROUTE = 135
DIRECTION_MUST_BE_2 = 136
DIRECTION_FORMAT_INCORRECT = 137
UNLINK_TRANSPORT_FIRST = 138
INVALID_FORMAT = 139
NOT_FOUND = 140

# /transport/organization/v1/drivers

NO_VALUES_TO_UPDATE = 300

# most likely user is not transport_admin but has scopes without real organization binded
NO_ORGANIZATION_TOKEN_PAYLOAD = 301

NAME_PARAMETER_REQUIRED = 302
EMAIL_OR_PHONE_PARAMETER_REQUIRED = 303

DRIVER_NOT_FOUND = 304

EMPTY_DRIVER_PARAMETERS = 305
TRANSPORT_AND_AVAILABLE_TRANSPORT_REQUIRED = 306
TRANSPORT_MUST_BE_IN_AVAILABLE_TRANSPORT = 307
AVAILABLE_TRANSPORT_MUST_BE_LIST_OF_INT = 308
TRANSPORT_MUST_BE_INT = 309


# /transport/driver/v1/points

LAT_LNG_PARAMETER_REQUIRED = 320
ID_PARAMETER_REQUIRED = 321
POINT_NOT_FOUND = 322
TRANSPORT_MUST_BE_LIST = 323

# /transport/organization/v1/notifications

NOTIFICATION_NOT_FOUND = 330
NO_VALUES_TO_PATCH = 331
TIME_BOUNDS_REQUIRED = 332

# /transport/organization/v1/notifications/report/*
UNKNOWN_NOTIFICATIONS_DOMAIN = 340

# /transport/box/*
ID_IS_INVALID = 360
VERSION_IS_NULL = 361


# /transport/v1/ssh
DEAD_TRANSPORT = 370
