from decouple import config

NAME = 'auth'
PREFIX = '/auth'

API_KEY = config('AUTH_API_KEY', cast=str)
