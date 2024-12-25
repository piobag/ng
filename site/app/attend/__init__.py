from datetime import datetime, timezone
from time import time, sleep
import requests
from bson.objectid import ObjectId

import jwt
import pytz
from flask import Blueprint, abort, current_app, render_template, url_for
from flask_login import current_user
from flask_mail import Message

from .. import db, mail
from ..finance import Payment, Devedor
from ..base import Event, File, User
from ..auth import notify

bp = Blueprint('attend', __name__)
tz = pytz.timezone('America/Sao_Paulo')

class Image(db.Document):
    img = db.ImageField(size=(2800, 2800, False), thumbnail_size=(200, 200, False))
    seq = db.IntField()
    s3 = db.StringField()
    rejected = db.BooleanField(default=False)
    confirmed = db.BooleanField(default=False)
    content_type = db.StringField()
    def delete_all(self):
        if self.img:
            self.img.delete()

        #! Apagar do S3

        self.delete()
    def to_dict(self):
        return {
            'id': str(self.id),
            'seq': self.seq,
            'rejected': self.rejected,
            'confirmed': self.confirmed,
        }
    def to_event(self):
        return {
            'img': str(self.img.grid_id) if self.img else None,
            'seq': self.seq,
            's3': self.s3,
            'rejected': self.rejected,
            'confirmed': self.confirmed,
            'content_type': self.content_type,
        }
# Nature Document
class Document(db.Document):
    name = db.StringField(required=True, unique=True)
    active = db.BooleanField(default=True)
    copia = db.BooleanField(default=False)
    qtd = db.IntField()
    meta = {'strict': False,
                'indexes': [{
                    'fields': ['$name'],
                    'weights': {'name': 3} }]}
    def to_list(self):
        return {
            'id': str(self.id),
            'name': str(self.name),
            'active': self.active,
        }
    def to_info(self):
        return {
            'id': str(self.id),
            'name': str(self.name),
            'active': self.active,
        }

class Nature(db.Document):
    name = db.StringField(required=True, unique=True)
    enabled = db.BooleanField(default=True)
    type = db.StringField()#required=True)
    group = db.StringField()#required=True)
    docs = db.ListField(db.ReferenceField(Document))
    meta = {'strict': False,
                'indexes': [{
                    'fields': ['$name'],
                    'weights': {'name': 3} }]
    }
    def to_info(self):
        info = {
            'id': str(self.id),
            'name': str(self.name),
            'type': self.type,
            'group': self.group,
            'docs': [{'id': str(x.id), 'name': str(x.name)} for x in self.docs],
        }
        return info

class Attend(db.Document):
    func = db.ReferenceField(User, required=True)
    user = db.ReferenceField(User, required=True)
    cred = db.ReferenceField(User)
    start = db.FloatField()
    end = db.FloatField()
    timestamp = db.FloatField(required=True)
    meta = {'strict': False}

    def delete_all(self):
        for s in Service.objects(attend=self.id):
            s.delete()
        for p in Payment.objects(attend=self.id):
            p.delete()
        self.delete()
    def to_event(self):
        return {
            'id': str(self.id),
            'user': str(self.user.id),
            'func': self.func.name,
            'start': self.start,
            'end': self.end,
        }
    def to_list(self):
        return {
            'id': str(self.id),
            'name': self.user.name,
            'cpf': self.user.cpfcnpj,
            'email': self.user.email,
            'end': self.end,
        }
    def to_dict(self):
        return {
            'id': str(self.id),
            'func': self.func.name,
            'name': self.user.name,
            'cpf': self.user.cpfcnpj,
            'email': self.user.email,
            'tel': self.user.tel,
            'start': self.start,
            'end': self.end,
        }
    def to_info(self):
        # Object Attend History
        history = [x.to_dict() for x in Event.objects(object='attend', target__id=str(self.id))]
        # # Services Attend History
        # for s in Service.objects(attend=self.id):
        #     for h in s.get_history():
        #         history.append(h)
        # Payments
        # payments = [str(x.id) for x in Payment.objects(attend=self.id).only('id')]
        # for p in payments:
        #     history += [x.to_dict() for x in Event.objects(object='payment', target__id=p)]
        # # Pagamentos Deletados
        # history += [x.to_dict() for x in Event.objects(object='payment', action='delete', target__attend=str(self.id))]

        # service_list = []
        # for s in Service.objects(attend=self.id):
        #     service_list.append(s.to_dict())
        #     ### Histórico dos serviços
        #     svc_history = s.get_history()
        #     # Exigencia
        #     svc_history += [x.to_dict() for x in Event.objects(action='create', object='exig', target__id=str(s.id))]
        #     # Docs adicionados no Prot
        #     svc_history += [x.to_dict() for x in Event.objects(action='create', object='docs', target__id=str(s.id))]
        #     history += svc_history

        # # Sort history
        # def sort_time(e):
        #     return e['timestamp']
        # history.sort(key=sort_time)
        # history.reverse()
        # if self.user.pj:
        #     services = 0.0
        #     for a in Attend.objects.filter(user=self.user):
        #         services += sum([x.paid for x in Service.objects.filter(attend=a.id).only('paid')])
        #     payments = sum([x.value for x in Payment.objects.filter(user=self.user, confirmed__ne=None, attend__ne=None).only('value')])
        #     deposits = sum([x.value for x in Payment.objects.filter(user=self.user, confirmed__ne=None, attend=None).only('value')])
        #     saldo = payments + deposits - services
        # else:
        #     services = sum([x.paid for x in Service.objects.filter(attend=self).only('paid')])
        #     payments = sum([x.value for x in Payment.objects.filter(attend=self, confirmed__ne=None).only('value')])
        #     saldo = payments - services
        return {
            'id': str(self.id),
            'func': self.func.name,
            'name': self.user.name,
            'cpf': self.user.cpfcnpj,
            'email': self.user.email,
            'tel': self.user.tel,
            'services': [x.to_info() for x in Service.objects(attend=self.id)],
            'start': self.start,
            'end': self.end,
            'history': history,
        }

# class Doc(db.DynamicDocument):
#     name = db.StringField()
#     entregue = db.BooleanField(required=True)
#     func_id = db.ReferenceField(User)
#     service = db.ReferenceField('Service')
#     timestamp = db.FloatField(required=True)
#     reg_time = db.DateTimeField()
#     copia = db.BooleanField(default=False)
#     imgs = db.ListField(db.ReferenceField(Image))
#     files = db.ListField(db.ReferenceField(File))
#     pending = db.BooleanField(default=False)
#     ready = db.BooleanField(default=False)
#     wait = db.BooleanField(default=False)
#     obs = db.StringField(max_length=256)
#     planta = db.BooleanField(default=False)
#     meta = {'strict': False,
#             # 'db_alias': 'doc',
#             'indexes': [{
#                         'fields': ['$prot', '$reg_time'],
#                         'weights': {'prot': 1, 'reg_time': 1} }]}
#     def to_dict(self):
#         return {
#             'id': str(self.id),
#             'timestamp': self.timestamp,
#             'name': self.name,
#             'entregue': self.entregue,
#             'copia': self.copia,
#         }
#     def reorder(self):
#         seqs = sorted([x['seq'] for x in self.imgs])
#         for i in range(0, len(seqs)):
#             for j in self.imgs:
#                 if j['seq'] == seqs[i]:
#                     if j.seq != i:
#                         j.seq = i
#                     break
#         self.save()
#     def delete_all(self):
#         event = Event(
#             actor = current_user.id,
#             action = 'delete',
#             object = 'dec',
#             target = self.to_dict(),
#             timestamp = datetime.utcnow().timestamp(),
#         )
#         for img in self.imgs:
#             img.delete_all()
#         self.delete()
#         event.save()

class Service(db.Document):
    # Atendimento
    attend = db.ReferenceField(Attend)    

    timestamp = db.FloatField(required=True)
    nature = db.ReferenceField(Nature)#, required=True)
    group = db.StringField()

    # Dados Protesto
    prot_cod = db.FloatField(required=True, unique=True)
    prot_date = db.FloatField()
    prot_emi = db.FloatField()
    prot_ven = db.FloatField()
    prot_esp = db.StringField()
    prot_fls = db.StringField()
    prot_liv = db.StringField()
    prot_num = db.FloatField()
    prot_val = db.FloatField()
    prot_tot_c = db.FloatField()
    prot_tot_p = db.FloatField()
    
    # Dados Endereço
    end_cep = db.FloatField()
    end_log = db.StringField()
    end_bai = db.StringField()
    end_cid = db.StringField()
    end_uf = db.StringField()


    # Status do gráfico
    s_ended = db.BooleanField()
    s_start = db.BooleanField()

    meta = {
        'strict': False,
        'indexes': [{
            'fields': ['$prot_cod'],
            'weights': {'prot_cod': 3},
        }]
    }
    def to_event(self):
        return {
            'id': str(self.id),
            'prot': self.prot_cod,
            'total': self.prot_val,
            'attend': str(self.attend.id) if self.attend else None,
        }
    def to_list(self):
        return {
            'id': str(self.id),
            'prot': self.prot_cod,
            'date': self.timestamp,
            'attend': str(self.attend.id) if self.attend else None,
        }
    # def get_history(self):
        # return [x.to_dict() for x in Event.objects(object='service', target__id=str(self.id))]
    # def to_dict(self):
    #     try:
    #         itm = self.intimacao
    #     except Exception:
    #         itm = None

    #     return {
    #         'id': str(self.id),
    #         'prot': self.prot,
    #         'type': self.type,
    #         'group': self.group,
    #         'timestamp': self.timestamp,

    #         'canceled': self.canceled,
    #         'rejected': self.rejected,

    #         'nature': self.nature.name if self.nature else '',
    #         'docs': [x.to_dict() for x in Doc.objects.filter(service=self.id)],
    #         'mat': self.mat,
    #         'selo': self.selo,
    #         'edital': self.edital,

    #         'total': self.total,
    #         'paid': self.paid,
    #         'options': self.options,

    #         's_ended': self.s_ended,
    #         's_nosign': self.s_nosign,
    #         's_imgpend': self.s_imgpend,
    #         's_noimg': self.s_noimg,
    #         's_nodoc': self.s_nodoc,

    #         'user': self.attend.user.name if self.attend else None,
    #         'itm': itm,
    #         'prot_date': self.prot_date,

    #         'name': current_app.config['BOOKING_SERVICES'][self.type]['name'] if current_app.config['BOOKING_SERVICES'].get(self.type) else None,

    #         'files': [x.to_dict() for x in File.objects(service=self.id)],
    #         'minuta_pending': self.minuta_pending,
    #         'minuta_wrong': self.minuta_wrong,
    #         'minuta': self.minuta.to_dict() if self.minuta else None,
    #         'minuta_printed': self.minuta_printed,
    #         'func': User.objects.get(id=str(Event.objects.get(action='create', object='service', target__id=str(self.id)).actor.id)).name,

    #         'exig': str(self.exig.id) if self.exig else None,
    #         'exig_resp': str(self.exig_resp.id) if self.exig_resp else None,

    #         'pessoa': self.pessoa.to_dict() if self.pessoa else None,
    #     }
    def to_info(self):
            # history = self.get_history()
            # # Exigencia
            # history += [x.to_dict() for x in Event.objects(action='create', object='exig', target__id=str(self.id))]
            # # Docs adicionados no Prot
            # history += [x.to_dict() for x in Event.objects(action='create', object='docs', target__id=str(self.id))]
        # # Payments
        # if self.attend:
        #     payments = [str(x.id) for x in Payment.objects(attend=self.attend).only('id')]
        #     for p in payments:
        #         history += [x.to_dict() for x in Event.objects(object='payment', target__id=p)]
        # elif self.intimacao:
        #     payments = [str(x.id) for x in Payment.objects(attend=self.intimacao).only('id')]
        #     for p in payments:
        #         history += [x.to_dict() for x in Event.objects(object='payment', target__id=p)]
        # Sort history
        # def sort_time(e):
        #     return e['timestamp']
        # history.sort(key=sort_time)
        # history.reverse()
        return {
            'id': str(self.id),
            'timestamp': self.timestamp,

            'prot_cod':  self.prot_cod if self.prot_cod else '',
            'prot_date':  self.prot_date if self.prot_date else '',
            'prot_emi':  self.prot_emi if self.prot_emi else '',
            'prot_ven':  self.prot_ven if self.prot_ven else '',
            'prot_esp':  self.prot_esp if self.prot_esp else '',
            'prot_fls':  self.prot_fls if self.prot_fls else '',
            'prot_liv':  self.prot_liv if self.prot_liv else '',
            'prot_num':  self.prot_num if self.prot_num else '',
            'prot_val':  self.prot_val if self.prot_val else '',
            'prot_tot_c':  self.prot_tot_c if self.prot_tot_c else '',
            'prot_tot_p':  self.prot_tot_p if self.prot_tot_p else '',
            'end_cep':  self.end_cep if self.end_cep else '',
            'end_log':  self.end_log if self.end_log else '',
            'end_bai':  self.end_bai if self.end_bai else '',
            'end_cid':  self.end_cid if self.end_cid else '',
            'end_uf':  self.end_uf if self.end_uf else '',

            'attend': str(self.attend.id) if self.attend else None,
            'user': self.attend.user.to_list() if self.attend else None,

        }
    # def send_mail(self, exig=False):
    #     if not exig:
    #         abort(400)
    #     if not (self.attend and self.attend.user.email):
    #         return {'error': 'Usuário do atendimento sem email'}
    #     title = 'Título em Exigência - Não responda, email exclusivo para envio de exigências.'
    #     token = jwt.encode(
    #         {'exig': str(self.id)},
    #         current_app.config['SECRET_KEY'],
    #         algorithm='HS256'
    #     )
    #     msg = Message(
    #         title,
    #         sender=current_app.config['MAIL_DEFAULT_SENDER'],
    #         recipients=[self.attend.user.email]
    #     )
    #     msg.body = render_template(
    #         'email.txt',
    #         title=title,
    #         token=token,
    #         exig=exig,
    #     )
    #     msg.html = render_template(
    #         'email.html',
    #         title=title,
    #         token=token,
    #         exig=exig,
    #     )
    #     if not current_app.debug or self.attend.user.email in current_app.config['MAIL_ADMIN']:
    #         try:
    #             mail.send(msg)
    #         except Exception as e:
    #             notify(f'Exception sending mail', e)
    #             sleep(5)
    #             mail.send(msg)
    # def delete_all(self, make_event=True):

    #     #!! Tratar devoluções vinculadas

    #     event = Event(
    #         timestamp = datetime.now(timezone.utc).timestamp(),
    #         actor = current_user.id if current_user else None,
    #         action = 'delete',
    #         object = 'service',
    #         target = self.to_list(),
    #     )
    #     # Minuta
    #     if self.minuta:
    #         to_del = File.objects.filter(id=self.minuta.id).first()
    #         if to_del:
    #             to_del.file.delete()
    #             to_del.delete()
    #     # Arquivos
    #     for f in File.objects(service=self.id):
    #         f.file.delete()
    #         f.delete()

    #     # # Pessoa
    #     # if self.pessoa:
    #     #     to_del = Devedor.objects.filter(id=self.pessoa.id).first()
    #     #     if to_del:
    #     #         to_del.delete_all()

    #     self.delete()
    #     if make_event:
    #         event.save()
    # def send_exigencia(self):
    #     token = jwt.encode(
    #         {'exig': str(self.id), 'exp': time() + 14400},
    #         current_app.config['SECRET_KEY'],
    #         algorithm='HS256')
        
    #     results = []
    #     msgs = []
    #     msgs.append(f'Olá {self.attend.user.name}')
    #     msgs.append(f'segue exigências do protocolo {self.prot}')
    #     msgs.append(f'Click no seguinte link para mais informações: { url_for("attend.resp_exig", token=token, _external=True) }')

    #     for m in msgs:
    #         r = requests.post(
    #             f'http://whats:5000/send',
    #             json={
    #                 'msg': m,
    #                 'tel': f'55{self.attend.user.tel}',
    #             },
    #         )
    #         # return r.text
    #         results.append(r.text)
    #     return results
    # def update_status(self):
    #     if self.s_ended:
    #         return
    #     noimg = False
    #     imgpend = False
    #     ready = True
    #     docs = Doc.objects.only('imgs').filter(service=self.id)
    #     if len(docs) == 0:
    #         self.s_ended = False
    #         self.s_nosign = False
    #         self.s_imgpend = False
    #         self.s_noimg = False
    #         self.nodoc = True
    #         self.save()
    #         return
    #     self.nodoc = False
    #     for doc in docs:
    #         if len(doc.imgs) == 0:
    #             ready = False
    #             noimg = True
    #         for img in doc.imgs:
    #             if not img.confirmed:
    #                 ready = False
    #                 imgpend = True
    #                 break
    #     if ready:
    #         self.s_nosign = True
    #         self.s_imgpend = False
    #         self.s_noimg = False
    #         self.s_nodoc = False
    #     else:
    #         self.s_nosign = False
    #         self.s_imgpend = False
    #         if imgpend:
    #             self.s_imgpend = True
    #         self.s_noimg = False
    #         if noimg:
    #             self.s_noimg = True
    #     self.save()
    # def docs_token(self, expires_in=14400): #4h (14400)
    #     entregue = True
    #     for d in Doc.objects(service=self.id).only('entregue'):
    #         if not d.entregue:
    #             entregue = False
    #     if entregue:
    #         return {'error': 'Serviço sem documentos faltantes'}
    #     token = jwt.encode(
    #         {'service': str(self.id), 'exp': time() + expires_in},
    #         current_app.config['SECRET_KEY'],
    #         algorithm='HS256',
    #     )
    #     return {'result': token}
    # def reorder(self):
    #     seqs = sorted([x['seq'] for x in self.imgs]) # [0, 2, 3]
    #     for i in range(0, len(seqs)):
    #         for j in self.imgs:
    #             if j['seq'] == seqs[i]:
    #                 if j.seq != i:
    #                     j.seq = i
    #                 break
    #     self.save()

from . import routes
