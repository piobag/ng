from flask import Blueprint

from .. import db

bp = Blueprint('audit', __name__)

class DevReport(db.Document):
    date = db.FloatField(required=True, unique=True)
    hours = db.IntField(required=True)
    doc = db.FileField(required=True)
    meta = {'strict': False}
    def to_dict(self):
        return {
            'id': str(self.id),
            'date': self.date,
            'hours': self.hours,
        }

from . import routes
