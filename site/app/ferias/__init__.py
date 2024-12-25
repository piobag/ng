from time import sleep
import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta

from flask import Blueprint
from flask_mail import Message
from flask import render_template, current_app

from .. import db, mail
from ..auth import notify
from ..base import User

bp = Blueprint('ferias', __name__)

tz = pytz.timezone('America/Sao_Paulo')

class Ferias(db.Document):
    user = db.ReferenceField(User, required=True)
    timestamp = db.FloatField(required=True)
    adm = db.ReferenceField(User)
    start = db.FloatField(required=True)
    end = db.FloatField(required=True)
    confirmed = db.BooleanField(default=False)
    rejected = db.BooleanField(default=False)
    meta = {'strict': False,
            'indexes': [{
                        'fields': ['$user'],
                        'weights': {'user': 1} }]}
    def send_mail(self):
        title = 'Solicitação de férias'
        msg = Message(
            title,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[self.user.email]
        )
        msg.body = render_template(
            'email.txt',
            title=title,
            ferias=self.to_dict(mail=True)
        )
        msg.html = render_template(
            'email.html',
            title=title,
            ferias=self.to_dict(mail=True)
        )
        if not current_app.debug or self.user.email in current_app.config['MAIL_ADMIN']:
            try:
                mail.send(msg)
            except Exception as e:
                notify(f'Exception sending mail', e)
                sleep(5)
                mail.send(msg)
    def to_dict(self, mail=False):
        return {
            'id': str(self.id),
            'user': self.user.name if self.user else '',
            'start': tz.localize(datetime.fromtimestamp(self.start)) if mail else self.start,
            'end': tz.localize(datetime.fromtimestamp(self.end)) if mail else self.end,
            #'days': (datetime.fromtimestamp(self.end) - datetime.fromtimestamp(self.start)).days + 1,
            'confirmed': self.confirmed,
            'rejected': self.rejected
        }

def verify_ferias(user, start, end):
    try:
        start = tz.localize(datetime.strptime(start, "%Y-%m-%d")).astimezone(pytz.utc).timestamp()
        end = tz.localize(datetime.strptime(end, "%Y-%m-%d")).astimezone(pytz.utc).timestamp()
    except:
        return {'error': 'Data em formato inválido'}, 400
    if start > end:
        return {'error': 'O dia final não pode ser antes do dia inicial'}, 400
    days = (datetime.fromtimestamp(end) - datetime.fromtimestamp(start)).days + 1
    if days < 5 or days > 30:
        return {'error': 'Quantidade inválida de dias.'}, 400
    if not user.admissao:
        return {'error': 'Funcionário sem data de admissão.'}, 400
    years = relativedelta(datetime.fromtimestamp(start), datetime.fromtimestamp(user.admissao)).years

    total_days = sum([(datetime.fromtimestamp(x.end) - datetime.fromtimestamp(x.start)).days + 1 for x in Ferias.objects(user=user.id, rejected=False)])
    diff = years * 30 - total_days
    if days > diff:
        return {'error': f'Apenas {diff} dias disponíveis'}
    if diff > 0:
        if diff >= 30: # Primeiro período
            pass
            # if days < 15:
            #     return {'error': 'O primeiro período deve ser maior que 15 dias'}
        remain = diff - days
        if remain != 0 and remain < 5: # Último período
            return {'error': f'O último período deve ser maior ou igual a 5 dias. Sobraram apenas {remain} dias.'}, 400
        newferias = Ferias(
            timestamp=datetime.utcnow().timestamp(),
            user=user.id,
            start=start,
            end=end,
        )
        try:
            newferias.save()
            return {'result': 'Pedido de férias salvo.'}
        except Exception as e:
            notify('Error saving to database', e)
            return {'error': 'Error saving to database'}, 400
    else:
        return {'error': 'Sem férias disponível. Solicite para uma data futura ou cancele solicitações existentes.'}, 400

from . import routes
