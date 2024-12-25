from datetime import datetime
from time import sleep
import pytz

import jwt
from flask import render_template, current_app
from flask_mail import Message
from flask import Blueprint

from .. import db, mail
from ..auth import notify
from ..base import User, Event, File

bp = Blueprint('finance', __name__)
tz = pytz.timezone('America/Sao_Paulo')

class Endereco(db.Document):
    estado = db.StringField()
    municipio = db.StringField()
    end = db.StringField(required=True)
    cep = db.StringField()
    meta = {'strict': False}
    def to_dict(self):
        return {
            'id': str(self.id),
            'estado': self.estado,
            'municipio': self.municipio,
            'end': self.end,
            'cep': self.cep,
        }

class Devedor(db.Document):
    name = db.StringField()
    cpf = db.StringField()
    genero = db.StringField()
    estcivil = db.StringField()
    intimado = db.BooleanField(default=False)
    falecido = db.BooleanField(default=False)
    # externo = db.BooleanField(default=False)
    # enderecos = db.ListField(db.ReferenceField(Endereco))
    meta = {'strict': False}
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'cpf': self.cpf,
            'genero': self.genero,
            'estcivil': self.estcivil or None,
            'intimado': self.intimado,
            'falecido': self.falecido,
        }
    def delete_all(self):
        # if self.enderecos:
        #     for e in self.enderecos:
        #         to_del = Endereco.objects.filter(id=e.id).first()
        #         if to_del:
        #             to_del.delete()
        self.delete()

class Account(db.Document):
    user = db.ReferenceField(User, required=True)
    banco = db.StringField()
    tipo = db.StringField(max_length=1, required=True)
    agencia = db.StringField()
    conta = db.StringField()

class Payment(db.Document):
    attend = db.ReferenceField('Attend')
    intimacao = db.ReferenceField('Intimacao')
    user = db.ReferenceField('User')
    func = db.ReferenceField('User')
    timestamp = db.FloatField(required=True)
    compr = db.ReferenceField(File)
    type = db.StringField(required=True)
    value = db.FloatField(required=True)
    confirmed = db.FloatField()
    parent = db.ReferenceField('self')
    meta = {
        'strict': False,
        'indexes': [
            'attend',
            'intimacao',
        ]    
    }
    def to_status(self):
        pass
        # # itm = Intimacao.objects().only()
        # desc = Event.objects.filter(
        #         action='comment',
        #         object='payment',
        #         target__id=str(self.id)
        # ).only('target').first()

        # return {
        #     'id': str(self.id),
        #     'type': current_app.config['PAYMENTS'][self.type]['name'],

        #     'attend': self.attend,
        #     'itm': self.intimacao,

        #     'value': self.value,
        #     'timestamp': self.timestamp,
        #     'confirmed': self.confirmed,
        #     'compr': str(self.compr.id) if self.compr else None,
        #     'desc': desc['target']['comment'] if desc else None,
        # }
    def to_event(self):
        return {
            'id': str(self.id),
            'type': self.type,
            # 'type': current_app.config['PAYMENTS'][self.type]['name'],

            'attend': str(self.attend.id) if self.attend else None,
            'itm': str(self.intimacao.id) if self.intimacao else None,

            'value': self.value,
            'confirmed': self.confirmed if self.confirmed else None,
            'compr': str(self.compr.id) if self.compr else None,
        }
    def to_dict(self):
        desc = Event.objects.filter(
                action='comment',
                object='payment',
                target__id=str(self.id)
        ).only('target').first()

        return {
            'id': str(self.id),
            'type': current_app.config['PAYMENTS'][self.type]['name'],

            'attend': self.attend,
            'itm': self.intimacao,

            'value': self.value,
            'timestamp': self.timestamp,
            'confirmed': self.confirmed if self.confirmed else None,
            'compr': str(self.compr.id) if self.compr else None,
            'desc': desc['target']['comment'] if desc else None,
        }
    def delete_all(self):
        # Arquivo do comprovante
        if self.compr:
            to_del = File.objects.filter(id=self.compr.id).first()
            if to_del:
                to_del.file.delete()
                to_del.delete()
        # Eventos
        for e in Event.objects(object='payment', target__id=str(self.id)):
            e.delete()
        self.delete()

class Devol(db.Document):
    func = db.ReferenceField(User, required=True)
    user = db.ReferenceField(User, required=True)
    service = db.ReferenceField('Service', required=True)

    value = db.FloatField(required=True)
    timestamp = db.FloatField(required=True)

    choice = db.StringField()
    check = db.FloatField()

    transf = db.FileField()
    retire = db.FileField()
    account = db.ReferenceField(Account)

    paid = db.BooleanField(default=False)
    meta = {'strict': False,
            'indexes': [{
                'fields': ['$value'],
                'weights': {'value': 1} }]}
    def to_dict(self):
        try:
            prot = self.service.prot
        except Exception as e:
            notify('Erro no devol', f'{self.id}, func {self.func.name}, user {self.user.name}, value {self.value}, time {datetime.fromtimestamp(self.timestamp)}\n{e}')
            prot = None
        return {
            'id': str(self.id),
            'cpf': self.user.cpfcnpj,
            'name': self.user.name,
            'prot': prot,
            'senddate': self.timestamp,
            'value': self.value,
            'choice': self.choice,
            'paid': self.paid,
        }
        # except Exception as e:
        #     print(e)
    def to_info(self):
        # try:
            data = {
                'id': str(self.id),
                'prot': self.service.prot,
                'nature': self.service.nature.name if self.service.__contains__('nature') else '',
                'senddate': self.timestamp,
                'value': self.value,
                'choice': self.choice,
                'paid': self.paid,
                'user': self.user.to_dict(),
            }
            if self.choice == 'transf':
                data['transf'] = Account.objects.get(id=self.account.id)
            if self.transf:
                data['file'] = 'true'
                # data['file'] = str(self.transf.grid_id)
                # print(data['file'])
            return data
        # except Exception as e:
        #     print(e)
        #     print(self.service.__contains__('nature'))
        #     # for k in self.keys():
        #     print(dir(self.service))
    def send_mail(self, retireok=False, transfok=False):
        title = 'Devolução de emolumentos'
        if retireok or transfok:
            token=False
        else:
            token = jwt.encode(
                {'devol': str(self.id)},
                current_app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        msg = Message(
            title,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[self.user.email]
        )
        msg.body = render_template(
            'email.txt',
            title=title,
            token=token,
            transfok=transfok,
            retireok=retireok,
            devol=self.to_dict()
        )
        msg.html = render_template(
            'email.html',
            title=title,
            token=token,
            transfok=transfok,
            retireok=retireok,
            devol=self.to_dict()
        )
        if not current_app.debug or self.user.email in current_app.config['MAIL_ADMIN']:
            try:
                mail.send(msg)
            except Exception as e:
                notify(f'Exception sending mail', e)
                sleep(5)
                mail.send(msg)
    def delete_all(self):
        if self.transf:
            self.transf.delete()
        if self.retire:
            self.retire.delete()
        try:
            if self.account:
                to_del = Account.objects.get(id=self.account.id) #.first()
                # if to_del:
                to_del.delete()
        except:
            notify('Account do Devol não encontrado', f'Devol {self.id}, func {self.func.name}, user {self.user.name}')
        self.delete()
from . import routes
from . import company
