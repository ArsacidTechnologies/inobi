# advertisement/v3/login



**Parameters**

    {
      "phone": string,
      "national_code": string,
      "connect": bool (optional, default=false)
    }
	
** Success Responses**

If user with these phone and national_code is registered. And device is registered too. And device is the exact user.device (Can login happen?):

    if `connect` in parameters was TRUE 

    {
	    "message": str,
	    "status": int (2**),
	    "data": {
		    "device": [DEVICE],
		    "user": [USER],  
		    "login": [LOGIN],    # This will be present, only if `connect`=true in parameters
		    "is_logined": True,
			"open_connection": "true",
			"connection_status": {
				"remaining_attempts": int,
				"remaining_seconds": int,
				"max_attempts": int;
				"max_seconds": int           # seconds, default=config.AD_USER_CONNECTION_DURATION.total_seconds()
			}
		}
    }
    
    if `connect` in parameters was FALSE
    
    {
	    "message": str,
	    "status": int (2**),
	    "data": {
		    "device": [DEVICE],
		    "user": [USER],
		    "is_logined": True,
			"open_connection": "true",
			"connection_status": {
				"remaining_attempts": int,
				"remaining_seconds": int,
				"max_attempts": int;
				"max_seconds": int           # seconds, default=config.AD_USER_CONNECTION_DURATION.total_seconds()
			}
		}
    }

** Error Responses**

If User and Device found but user has reached to the max connection per day:

	{
		"message": "User has used max logins and connections. Try later.",
		"status": int (4**),  
		"error_code": 1014,   # (MAX_CONNECTION_REACHED = 1014),
		"data": {
			"is_logined": False,
			"open_connection": "false",
			"connection_status": {
				"remaining_attempts": int,
				"remaining_seconds": int,
				"max_attempts": int;
				"max_seconds": int           # seconds, default=config.AD_USER_CONNECTION_DURATION.total_seconds()
			}
		}
	}

If no user found or no device found:

	{
		"message": "User/Device not found.",
		"status": int (4**),  
		"error_code": 1015,  # (USER_OR_DEVICE_NOT_FOUND = 1015),
		"data": {
			"is_logined": False,
			"open_connection": "false",
			"connection_status": {}
		}
	}

If Shahkar failed, 

	{
		"message": string,
		"status": int (4**),  
		"error_code": 1002,  # (SHAHKAR_CHECK_FAILED = 1002)
		"data": {
			"is_logined": False,
			"open_connection": "false",
			"connection_status": {}
		}
	}
	

# advertisement/v3/connection/status/

**Parameters**

    {
      "phone": string,
      "national_code": string,
    }
	
** Success Responses**

If user with these phone and national_code is registered. And device is registered too. And device is the exact user.device (Can login happen?):

    {
	    "message": str,
	    "status": int (2**),
	    "data": {
		    "device": [DEVICE],
		    "user": [USER],  
			"open_connection": "true",
			"connection_status": {
				"remaining_attempts": int,
				"remaining_seconds": int,
				"max_attempts": int,
				"max_seconds": int           # seconds, default=config.AD_USER_CONNECTION_DURATION.total_seconds()
			}
		}
    }

** Error Responses**

If User and Device found but user has reached to the max connection per day:

	{
		"message": "User has used max logins and connections. Try later.",
		"status": int (4**),  
		"error_code": 1014,   # (MAX_CONNECTION_REACHED = 1014),
		"data": {
			"open_connection": "false",
			"connection_status": {
				"remaining_attempts": int,
				"remaining_seconds": int,
				"max_attempts": int;
				"max_seconds": int           # seconds, default=config.AD_USER_CONNECTION_DURATION.total_seconds()
			}
		}
	}

If no user found or no device found:

	{
		"message": "User/Device not found.",
		"status": int (4**),  
		"error_code": 1015,  # (USER_OR_DEVICE_NOT_FOUND = 1015),
		"data": {
			"open_connection": "false",
			"connection_status": {}
		}
	}

If Inputs were failed, 

	{
		"message": string,
		"status": int (4**),  
		"error_code": 1009|1010,  # (PHONE_IS_NOT_VALID = 1009, NATIONAL_CODE_NOT_VALID = 1010)
		"data": {
			"open_connection": "false",
			"connection_status": {}
		}
	}
	

# advertisement/v3/send

**Parameters**

    {
      "phone": string,
      "national_code": string,
    }
	
** Success Responses**


If user is not registered or device is not registered or both:

    {
        "message": "OK",
        "status": int (2**),
        "data": {
		    "is_otp_sent": "true",
			"otp_status": {
				"send_code_attempt": {
					"status_code": 704,
					"total_requests": None,
					"block_duration": None,
					"is_blocked": False
				},
				"verify_code_attempt": {
					"status_code": 704,
					"total_requests": None,
					"block_duration": None,
					"is_blocked": False
				}
			}
        }
    }

** Error Responses**

If user found and device found:

	{
		"message": "User is already registered. Login.",
		"status": 400,  
		"error_code": 1007,  # (USER_ALREADY_REGISTERED = 1015),
		"data": {
			"is_otp_sent": "false",
			"otp_status": {}
		}
	}

if OTP Sending failed:
	
	{
		"message": string,
		"status": int (4**),  
		"error_code": 1003,  # (OTP_SEND_FAILED = 1003)
		"data": {
			"is_otp_sent": "false",
			"otp_status": {
				"send_code_attempt": {
					"status_code": 704,
					"total_requests": None,
					"block_duration": None,
					"is_blocked": False
				},
				"verify_code_attempt": {
					"status_code": 704,
					"total_requests": None,
					"block_duration": None,
					"is_blocked": False
				}
			}
		}
	}
	
If Shahkar failed, 

	{
		"message": string,
		"status": int (4**),  
		"error_code": 1002,  # (SHAHKAR_CHECK_FAILED = 1002)
		"data": {
			"is_otp_sent": false,
			"otp_status": {}
		}
	}
	
	

# advertisement/v3/verify

**Parameters**

    {
		"phone": str,
		"national_code": str,
		"code": str
    }
	
**Success Responses**
If OTP code validated successfully and user is not registered at all:

    {
	    "message": "Code validated successfully.Register",
	    "status": 200,  
		"data": {
			"need_register": "true",
			"is_code_valid": "true",
			"otp_status": {
				"send_code_attempt": {
					"status_code": 704,
					"total_requests": int,
					"block_duration": int,
					"is_blocked": 'false'
				},
				"verify_code_attempt": {
					"status_code": 704,
					"total_requests": None,
					"block_duration": None,
					"is_blocked": 'false'
				}
			}
		}
    }

If OTP code validated successfully and user was registered but device is not registered or related:

	{
		"message": "Code validated and device updated successfully.",
		"status": 200,  
		"data": {
			"need_register": "false",
			"is_code_valid": "true",
			"otp_status": {
				"send_code_attempt": {
					"status_code": 704,
					"total_requests": int,
					"block_duration": int,
					"is_blocked": 'false'
				},
				"verify_code_attempt": {
					"status_code": 704,
					"total_requests": None,
					"block_duration": None,
					"is_blocked": 'false'
				}
			}
		}
	}

**Error Responses**

If Shahkar check failed:

    {
		"message": string,
		"status": int (4--),  
		"error_code": 1002,    // (SHAHKAR_CHECK_FAILED = 1002)
		"data": {
			"need_register": 'false',
			"is_code_valid": "false",
			"otp_status": {}
		}
	}

if user were registered, device were registered and verified and *user==device.user*:

    {
		"message": "User is already registered. Login.",
		"status": int (4--),  
		"error_code": 1007,    // (USER_ALREADY_REGISTERED = 1007)
		"data": {
			"need_register": 'false',
			"is_code_valid": "false",
			"otp_status": {}
		}
	}

If code were empty or it was not the one that we send on his/her phone (invalid):

	{
		"message": str,
		"status": int (4--),  
		"error_code": 1004,    // (OTP_CHECK_FAILED = 1004)
		"data": {
			"need_register": 'false',
			"is_code_valid": "false",
			"otp_status": {
				"send_code_attempt": {
					"status_code": 704,
					"total_requests": None,
					"block_duration": None,
					"is_blocked": False
				},
				"verify_code_attempt": {
					"status_code": 704,
					"total_requests": None,
					"block_duration": None,
					"is_blocked": False
				}
			}
		}
	}
	

# advertisement/v3/register

**Parameters**

    {
		"phone": str,
		"national_code": str,
		"fname": str,
		"lname": str,
		"gender" : 969|696|null  //(969 Man) (696 Women),
		"birthday" : float|str (unix epoch or %Y-%m-%d)  //(969 Man) (696 Women),
    }


**Success Responses**
If Registration completed successfully:

    {
	    "message": "Register completed ...",
	    "status": 201,  
    }

**Error Responses**

If Shahkar check failed:

    {
		"message": string,
		"status": int (4--),  
		"error_code": 1002,    // (SHAHKAR_CHECK_FAILED = 1002)
	}

if user were registered, or another user with same phone or same national_code, raises the UniqueException:

    {
		"message": str,
		"status": int (4--),  
		"error_code": 1007,    // (USER_ALREADY_REGISTERED = 1007)
	}

If device create or update failed:

	{
		"message": str,
		"status": int (4--),  
		"error_code": 1011|1012, // (DEVICE_UPDATE_FAILED = 1011) (DEVICE_CREATE_FAILED = 1012)
	}
