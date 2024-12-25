import pytz

from flask import Blueprint
from mongoengine.connection import get_db
import gridfs

from .. import db
from ..base import User, Event, File
from ..attend import Service
from ..finance import Payment, Devedor, Endereco

bp = Blueprint('itm', __name__)

tz = pytz.timezone('America/Sao_Paulo')
fs = gridfs.GridFS(get_db())

# class Visit(db.Document):
#     func = db.ReferenceField(User, required=True)
#     date = db.FloatField(required=True)
#     timestamp = db.FloatField(required=True)
#     file = db.ReferenceField(File)

class Credor(db.Document):
    name = db.StringField(unique=True)
    cnpj = db.StringField(unique=True)
    sede = db.StringField()
    meta = {'strict': False}
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'cnpj': self.cnpj,
            'sede': self.sede,
        }

class Visita(db.Document):
    end = db.ReferenceField(Endereco, required=True)
    dev = db.ReferenceField(Devedor, required=True)
    date = db.FloatField(required=True)
    result = db.StringField(required=True)
    comment = db.StringField()
    timestamp = db.FloatField(required=True)
    meta = {
        'strict': False,
        'indexes': [
            'end',
            'dev',
        ]   
    }
    def to_event(self):
        return {
            'id': str(self.id),
            'date': self.date,
            'dev': str(self.dev.name),
            'result': self.result,
            'timestamp': self.timestamp,
        }
    def to_dict(self):
        return {
            'id': str(self.id),
            'date': self.date,
            'end': self.end.to_dict(),
            'dev': str(self.dev.name),
            'result': self.result,
            'comment': self.comment,
            'timestamp': self.timestamp,
        }


class Intimacao(db.Document):
    func = db.ReferenceField(User, required=True)
    cod = db.StringField(required=True, unique=True)
    prot_date = db.FloatField()
    services = db.ListField(db.ReferenceField('Service'))
    orcado = db.FloatField()

    # Status do gráfico
    s_ended = db.BooleanField()
    s_nodecu = db.BooleanField()
    s_nodili = db.BooleanField()
    s_visit3 = db.BooleanField()
    s_visit2 = db.BooleanField()
    s_visit1 = db.BooleanField()
    s_noprint = db.BooleanField()
    s_nosign = db.BooleanField()
    s_fix = db.BooleanField()
    s_minuta = db.BooleanField()
    s_protpend = db.BooleanField()
    s_noprot = db.BooleanField()
    s_nopaid = db.BooleanField()
    s_edital = db.BooleanField()
    s_public = db.BooleanField()

    # Ainda tem até o Serviço ser criado
    mat = db.StringField()

    credor = db.ReferenceField(Credor)
    pessoas = db.ListField(db.ReferenceField(Devedor))
    enderecos = db.ListField(db.ReferenceField(Endereco))
    contr = db.StringField()
    end = db.FloatField()
    # payment = db.ListField(db.ReferenceField('Payment'))

    timestamp = db.FloatField(required=True)
    meta = {'strict': False,
            'indexes': [{
                'fields': ['$cod'],
                'weights': {'cod': 1} }]}
    def to_list(self):
        return {
            'id': str(self.id),
            'cod': self.cod,
            'timestamp': self.timestamp,
        }
    def to_dict(self):
        return {
            'id': str(self.id),
            'cod': self.cod,
            'mat': self.mat,
            'timestamp': self.timestamp,
            'payments': [x.to_dict() for x in Payment.objects(intimacao=self.id)],
            'credor': self.credor.to_dict() if self.credor else None,
            'pessoas': [x.to_dict() for x in self.pessoas],
            'enderecos': {str(x.id):x.to_dict() for x in self.enderecos},
            'contr': self.contr,
            'prot_date': self.prot_date,
        }
    def to_info(self):
        pessoas = [x.to_dict() for x in self.pessoas]
        for i in range(0, len(pessoas)):
            pessoas[i]['visits'] = [x.to_dict() for x in Visita.objects(dev=pessoas[i]['id'])]
        history = [x.to_dict() for x in Event.objects(object='itm', target__id=str(self.id))]
        ## Services
        services = []
        for s in Service.objects(intimacao=self.id):
            services.append(s.to_dict)
            for h in s.get_history():
                history.append(h)
            # Minutas
            for m in Event.objects(object='minuta', target__id=str(s.id)):
                history.append(m.to_dict())
        # Deleted Services
        for d in Event.objects(action='delete', target__itm=str(self.id)):
            history.append(d.to_dict())
        ## Payments
        payments = [str(x.id) for x in Payment.objects(intimacao=self.id).only('id')]
        for p in payments:
            history += [x.to_dict() for x in Event.objects(object='payment', target__id=p)]
        # Endereços
        for e in self.enderecos:
            # History Visitas
            history += [x.to_dict() for x in Event.objects(object='visita', target__id=str(e.id))]

        # Sort history
        def sort_time(e):
            return e['timestamp']
        history.sort(key=sort_time)
        history.reverse()
        
        return {
            'id': str(self.id),
            'cod': self.cod,
            'mat': self.mat,
            'credor': self.credor.to_dict() if self.credor else None,
            'pessoas': pessoas,
            'enderecos': {str(x.id):x.to_dict() for x in self.enderecos},
            'contr': self.contr,
            's_ended': self.s_ended,
            's_nodecu': self.s_nodecu,
            's_nodili': self.s_nodili,
            's_visit3': self.s_visit3,
            's_visit2': self.s_visit2,
            's_visit1': self.s_visit1,
            's_noprint': self.s_noprint,
            's_nosign': self.s_nosign,
            's_fix': self.s_fix,
            's_minuta': self.s_minuta,
            's_protpend': self.s_protpend,
            's_noprot': self.s_noprot,
            's_nopaid': self.s_nopaid,
            's_edital': self.s_edital,
            's_public': self.s_public,
            'func': self.func.name,
            'timestamp': self.timestamp,
            'files': [x.to_dict() for x in File.objects(itm=self.id)],
            'services': [x.to_dict() for x in Service.objects(intimacao=self.id)],
            'payments': [x.to_dict() for x in Payment.objects(intimacao=self.id)],
            'orcado': self.orcado,
            'end': self.end,
            'history': history,
            'prot_date': self.prot_date,
        }
    def delete_all(self):
        # Eventos
        for e in Event.objects(object='itm', target__id=str(self.id)):
            e.delete()
        # Arquivos
        for f in File.objects(itm=self.id):
            f.file.delete()
            f.delete()
        # Serviços
        for s in Service.objects(intimacao=self.id):
            s.delete_all(make_event=False)
        # Pagamentos
        for p in Payment.objects(intimacao=self.id):
            p.delete_all()
        # Devedores
        if self.pessoas:
            for d in self.pessoas:
                to_del = Devedor.objects.filter(id=d.id).first()
                if to_del:
                    to_del.delete_all()
        # Endereços
        if self.enderecos:
            for e in self.enderecos:
                to_del = Endereco.objects.filter(id=d.id).first()
                if to_del:
                    to_del.delete()
        self.delete()

from . import routes
