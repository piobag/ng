import pytz
from os import path
from functools import wraps

from flask import Blueprint, request, current_app

bp = Blueprint('base', __name__)

from .. import db
from ..auth import User as AuthUser
from ..auth import Role, RoleBind

tz = pytz.timezone('America/Sao_Paulo')

class User(AuthUser):
    lunch = db.StringField()
    admissao = db.FloatField()

#     login_count = db.IntField()
#     last_login_at = db.DateTimeField()
#     current_login_at = db.DateTimeField()
#     last_login_ip = db.StringField()
#     current_login_ip = db.StringField()

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'cpfcnpj': self.cpfcnpj if self.cpfcnpj else '',
            'roles': [x.role.name for x in RoleBind.objects(user=self.id).only('role')],
            'tel': self.tel if self.tel else '',
            'admissao': self.admissao,
            'lunch': self.lunch,
            'email': self.email,
        }

class Event(db.Document):
    timestamp = db.FloatField(required=True)
    actor = db.ReferenceField(User)
    action = db.StringField()
    object = db.StringField()
    target = db.DictField()
    meta = {'strict': False}
    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'actor': self.actor.name,
            'action': self.action,
            'object': self.object,
            'target': self.target
        }

class File(db.Document):
    file = db.FileField()
    name = db.StringField(required=True)
    content_type = db.StringField()
    timestamp = db.FloatField(required=True)
    user = db.ReferenceField(User, required=True)

    service = db.ReferenceField('Service')
    itm = db.ReferenceField('Intimacao')
    attend = db.ReferenceField('Attend')
    meta = {'strict': False}
    def to_dict(self):
        return {
            'id': str(self.id),
            'grid_id': str(self.file.grid_id),
            'name': self.name,
            'type': self.content_type,
            'date': self.timestamp,
            'service': str(self.service.id) if self.service else None,
            'itm': str(self.itm.id) if self.itm else None,
            'user': self.user.name,
        }


def get_datatable(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        dt = {}
        dt['start'] = request.args.get('start', 0, type=int)
        dt['length'] = request.args.get('length', 5, type=int)
        dt['search'] = request.args.get('search', False)
        dt['filter'] = request.args.get('filter', None)

        return f(dt, *args, **kwargs)
    return wrapped


# Init  database
@bp.get('/init')
def init():
    ### Init Credores
    from ..itm import Credor
    credores = current_app.config['CREDORES']
    for c in credores:
        if not Credor.objects.filter(name=c['name']).only('id').first():
            print('Criando Credor')
            Credor(**c).save()

    ### Init Roles
    roles = current_app.config['AUTH_ROLES']
    for r in roles:
        if not Role.objects.filter(name=r).only('id').first():
            print('Creating Role')
            Role(name=r, text=roles[r]).save()

    ### Init Certificates
    serventia = current_app.config['SERVENTIA']
    if not path.isfile(serventia['CERT_CRT']):
        from ..crypt import generate_certificate
        generate_certificate(serventia['CERT_CRT'], serventia['CERT_KEY'])

    ### Update Estados/Municipios
    from .estados import update_ufs
    update_ufs()


    # from ..attend import Service
    # ### Mostrar info do Service
    # def show_service(service):
    #     print(service.get('prot'))
    #     print(service.get('initmacao'))
    #     print(service.get('func'))

    #     # print(datetime.fromtimestamp(service.get('timestamp')))

    #     # print(service.get('prot'))
    #     # print(service.get('prot'))


    # ### Services com ID de Natureza antiga
    # for s in Service.objects():
    #     try:
    #         if s.nature:
    #             s.nature.name
    #     except db.DoesNotExist as e:
    #         from mongoengine.connection import get_db
    #         mongo = get_db()
    #         coll = mongo['service']
            
    #         for s in coll.find():
    #             if not s.get('nature'):
    #                 print('Service sem Nature')
    #                 show_service(s)
    #                 continue
    #             if not Service.objects.filter(id=s.get('nature')).first():
    #                 print('Nature inexistente')
    #                 show_service(s)            


    return 'OK'

@bp.get('/fix')
def fix():
    if current_app.debug:
        from app.attend import Service
        for i in Service.objects():
            i.update_status()
    return 'Ok'

from . import routes
from . import estados
