from flask import Blueprint

from .. import db

bp = Blueprint('popup', __name__)

class Popup(db.Document):
    name = db.StringField()
    route = db.StringField()
    active = db.BooleanField()
    file = db.FileField()
    meta = {'strict': False}

from . import routes