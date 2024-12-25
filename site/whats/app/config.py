import secrets
from os import getenv
from datetime import timedelta

class Config(object):
    TITLE = getenv('TITLE')
    SECRET_KEY = getenv('SECRET_KEY') or secrets.token_urlsafe()

    MAIL_ADMIN = getenv('MAIL_ADMIN', '').split(',')
    MAIL_USERS = getenv('MAIL_USERS', '').split(',')
    MAIL_CONTACT = getenv('MAIL_CONTACT', '').split(',')
    MAIL_DEFAULT_SENDER = f"{getenv('TITLE')} - Não responda <{getenv('MAIL_USERNAME')}>"

    DOMAIN = getenv('DOMAIN')

    SESSION_COOKIE_DOMAIN = f".{DOMAIN}"
    REMEMBER_COOKIE_DOMAIN = f".{DOMAIN}"

    MAIL_SERVER = getenv('MAIL_SERVER')
    MAIL_USERNAME = getenv('MAIL_USERNAME')
    MAIL_PASSWORD = getenv('MAIL_PASSWORD')
    MAIL_PORT = int(getenv('MAIL_PORT') or 587)
    MAIL_USE_TLS = getenv('MAIL_USE_TLS') or True

