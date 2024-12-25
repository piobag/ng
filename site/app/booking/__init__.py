from time import sleep
from datetime import datetime

from flask import Blueprint, render_template, current_app
from flask_mail import Message
import pytz

from .. import db, mail
from ..auth import User, notify

bp = Blueprint('booking', __name__)
tz = pytz.timezone('America/Sao_Paulo')

class Booking(db.Document):
    timestamp = db.FloatField(required=True)
    user = db.ReferenceField(User, required=True)
    func = db.ReferenceField(User, required=True)
    start = db.FloatField(required=True)
    attend = db.ReferenceField('Attend')
    name = db.StringField()
    services = db.DictField()
    obs = db.StringField()
    meta = {'strict': False}
    def to_dict(self, mail=False):
        return {
            'id': str(self.id),
            'name': self.name,
            'start': tz.localize(datetime.fromtimestamp(self.start)) if mail else self.start,
            'services': self.services,
            'func': self.func.name,
            'obs': self.obs
        }
    def send_mail(self, delete=False, reason=None):
        if delete:
            title = 'Cancelamento de atendimento'
            self.delete()
        else:
            title = 'Novo atendimento agendado'
        msg = Message(
            title,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[self.user.email]
        )
        msg.body = render_template(
            'email.txt',
            booking=self.to_dict(mail=True),
            delete=delete,
            reason=reason,
            title=title
        )
        msg.html = render_template(
            'email.html',
            booking=self.to_dict(mail=True),
            delete=delete,
            reason=reason,
            title=title
        )
        if not current_app.debug or self.user.email in current_app.config['MAIL_ADMIN']:
            try:
                mail.send(msg)
            except Exception as e:
                notify(f'Exception sending mail', e)
                sleep(5)
                mail.send(msg)

class Blacklist(db.Document):
    name = db.StringField(required=True)
    user = db.ReferenceField(User, required=True)
    start = db.FloatField()
    end = db.FloatField()
    meta = {'strict': False}


from . import routes
