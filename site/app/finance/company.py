import re
from os import path, getenv
from datetime import datetime, date
from importlib import import_module
import pytz
import base64
from io import BytesIO

import jwt
from werkzeug.utils import secure_filename
from flask import render_template, request, current_app, abort, send_file
from flask_login import current_user, login_required
from flask_babel import _
from mongoengine.queryset.visitor import Q

from .. import db

from . import bp, Devol
from ..attend import Attend, Nature, Service
from ..finance import Payment, Account
from ..auth import get_roles, check_roles, get_json, notify
from ..auth.cpfcnpj import verify_cpfcnpj
from ..base import File, Event, User
from ..itm import Intimacao

tz = pytz.timezone('America/Sao_Paulo')

class CompanyBind(db.Document):
    company = db.ReferenceField(User, required=True)
    user = db.ReferenceField(User, required=True)
    file = db.ReferenceField(File, required=True)
    timestamp = db.FloatField(required=True)

    # meta = {'strict': False}

    def to_list(self):
        return {
            'id': str(self.id),
            'user': self.user.name,
            'company': self.company.name,
        }

    # def to_list(self):
    #     return {
    #         'id': str(self.id),
    #         'cpfcnpj': self.cpfcnpj if self.cpfcnpj else '',
    #         'name': self.name,
    #         'email': self.email,
    #     }
    # def get_services(self):
    #     result = []
    #     attends = Attend.objects.filter(user=self.id).only('id')
    #     for a in attends:
    #         services = Service.objects.filter(attend=a.id).limit(5)
    #         for s in services:
    #             result.append(s.to_list())
    #     return result
    # def to_dict(self):
    #     users = []
    #     for u in self.users:
    #         file = File.objects.filter(company=self.id, user=u.id).first()
    #         if file:
    #             users.append({**u.to_list(), 'file': str(file.id)})
    #         else:
    #             users.append(u.to_list())
    #     # Balance
    #     cred = sum([x.value for x in Payment.objects.filter(user=self.id, confirmed__ne=None)])
    #     deb = 0.0
    #     attends = Attend.objects.filter(user=self.id).only('id')
    #     for a in attends:
    #         services = Service.objects.filter(attend=a.id).only('paid')
    #         for s in services:
    #             deb += s.paid
    #     balance = cred-deb
    #     result = {
    #         'id': str(self.id),
    #         'cpfcnpj': self.cpfcnpj if self.cpfcnpj else '',
    #         'name': self.name,
    #         'email': self.email,
    #         'tel': self.tel if self.tel else '',
    #         'users': users,
    #         'payments': [x.to_dict() for x in Payment.objects(user=self.id).limit(5)],
    #         'services': self.get_services(),
    #         'balance': balance,
    #     }
    #     # history = [x.to_dict() for x in Event.objects(action='comment', object='payment', target__id=str(self.id))]
    #     # def sort_time(e):
    #     #     return e['timestamp']
    #     # history.sort(key=sort_time)
    #     # history.reverse()
        
    #     return result




@bp.post('/company')
@login_required
@check_roles(['fin'])
@get_json
def post_company(data):
    # Client Check
    email = data['email'].strip().lower()
    if not re.fullmatch('^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*@(?:\w+\.)+[A-Za-z0-9]+$', email):
        return {'error': _('Enter a valid email address')}, 400
    cnpj = re.sub('\D', '', data['cnpj'])
    if not verify_cpfcnpj(cnpj):
        return {'error': _('Invalid CNPJ')}, 400

    # DB Check
    # if User.objects.filter(email=email).first():
    #     return {'error': _('Email already registered with a User')}, 400
    if User.objects.filter(cpfcnpj=cnpj).first():
        return {'error': _('CNPJ already registered with a User')}, 400
    
    dict = {
        'cpfcnpj': cnpj,
        'pj': True,
        'name': data['name'].strip().upper(),
        'email': email,
        'tel': re.sub('\D', '', data['tel']),
        'timestamp':  datetime.utcnow().timestamp(),
    }
    company = User(**dict)
    try:
        company.save()
        if not current_app.debug:
            try:
                company.send_mail(confirm=True)
            except Exception as e:
                notify(f"{_('Error saving user')} {cnpj}", e)
                company.delete()
                return {'error': f'Falha ao enviar o email para {email}, tente novamente.'}
        return {'result': 'ok'}
    except Exception as e:
        msg = f"{_('Error saving to database')}: new company"
        notify(msg, e)
        return {'error': msg}, 400

@bp.get('/companys')
@login_required
@check_roles(['fin'])
def get_companys():
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 5, type=int)

    filter = request.args.get('filter')
    # if filter:
    #     if filter == 'waiting':
    #         total_filtered = CompanyBind.objects(choice=None).count()
    #         list = CompanyBind.objects(choice=None).skip(start).limit(length).order_by('-timestamp')
    # search = request.args.get('search')
    # if search:
    #     total_filtered = CompanyBind.objects.search_text(search).count()
    #     list = CompanyBind.objects.search_text(search).skip(start).limit(length).order_by('-timestamp')
    # else:
    #     total_filtered = CompanyBind.objects().count()
    #     list = CompanyBind.objects().skip(start).limit(length).order_by('-timestamp')
    # order = []
    # i = 0
    # while True:
    #     col_index = request.args.get(f'order[{i}][column]')
    #     if col_index is None:
    #         break
    #     col_name = request.args.get(f'columns[{col_index}][data]')
    #     if col_name not in ['name', 'email', 'prot']:
    #         col_name = 'name'
    #     descending = request.args.get(f'order[{i}][dir]') == 'desc'
    #     if descending:
    #         col = f'-{col_name}'
    #     else:
    #         col = col_name
    #     # col = getattr(User, col_name)
    #     # if descending:
    #     #     col = col.desc()
    #     order.append(col)
    #     i += 1
    # if order:
    #     list = list.order_by(*order)

    total_filtered = User.objects(pj=True).count()
    list = User.objects(pj=True).skip(start).limit(length).order_by('-timestamp')
    return {
        'result': [x.to_list() for x in list],
        'total': total_filtered,
    }

@bp.get('/company')
@login_required
@check_roles(['fin'])
def get_company():
    id = request.args.get('id')
    if not (id and len(id) == 24):
        abort(400)
    company = User.objects.get_or_404(id=id, pj=True)
    result = company.to_list()
    # Credenciados
    user_map = {}
    for cbind in CompanyBind.objects(company=company).only('user'):
        if not str(cbind.user.id) in user_map:
            user_map[str(cbind.user.id)] = cbind.user.to_list()
    result['users'] = [x for x in user_map.values()]
    # Pagamentos
    result['payments'] = [x.to_dict() for x in Payment.objects(user=id)]
    # Serviços
    result['services'] = []
    attends = Attend.objects.filter(user=id).only('id')
    for a in attends:
        services = Service.objects.filter(attend=a.id).limit(5)
        for s in services:
            result['services'].append(s.to_list())
    return {'result': result}

@bp.post('/company/user')
@login_required
@check_roles(['fin'])
@get_json
def post_company_user(data):
    id = data.get('id')
    file = data.get('compr')
    if not (id and len(id) == 24 and file and file.get('data')):
        abort(400)
    company = User.objects.filter(id=id, pj=True).first()
    if not company:
        return {'error': 'Empresa não encontrado'}, 400
    user = User.objects.get_or_404(cpfcnpj=data['user']) if data.get('user') else False
    if not user:
        return {'error': 'Usuário não encontrado'}, 400
    if CompanyBind.objects.filter(user=user.id, company=company.id).first():
        return {'error': 'Usuário já cadastrado'}, 400
    # Novo CompanyBind
    cbind = CompanyBind(
        user=user,
        company=company,
        timestamp=datetime.utcnow().timestamp(),
    )
    # Arquivo
    filename = secure_filename(file['fileName'])
    newfile = File(
        user = user.id,
        name = filename,
        content_type = file['fileType'],
        timestamp = datetime.utcnow().timestamp(),
    )
    content = base64.b64decode(file['data'])
    bcontent = BytesIO(content)
    newfile.file.put(bcontent, app='company', filename=filename, content_type=file['fileType'])
    newfile.save()
    # Arquivo no Bind
    cbind.file = newfile
    cbind.save()

    target = {'id': str(company.id), 'user': str(user.id)}
    event = Event(
        actor = current_user.id,
        action = 'bind_user',
        object = 'company',
        target = target,
        timestamp = datetime.utcnow().timestamp(),
    )
    event.save()
    return {'result': 'ok'}

@bp.get('/company/user')
@login_required
@check_roles(['fin'])
def get_company_user():
    id = request.args.get('id')
    user = request.args.get('user')
    if not id or len(id) < 12 or not user:
        abort(400)
    result = CompanyBind.objects.get_or_404(company=id, user=user)
    return send_file(
        result.file.file.get(),
        mimetype=result.file.file.content_type,
    )


@bp.delete('/company/user')
@login_required
@check_roles(['fin'])
@get_json
def delete_company_user(data):
    id = data.get('id')
    user_cpf = data.get('user')
    if not (id and len(id) == 24 and user_cpf):
        abort(400)
    user = User.objects.get_or_404(cpfcnpj=user_cpf)
    company = Company.objects.get_or_404(id=id)
    if not user in company.users:
        return {'error': 'Usuário não cadastrado na empresa'}, 400
    company.users.remove(user)
    company.save()
    return {'result': 'ok'}

@bp.post('/company/payment')
@login_required
@check_roles(['fin'])
@get_json
def post_company_payment(data):
    id = data.get('id')
    if not (id and len(id) == 24):
        abort(400)
    value = data.get('value')
    if not (value and value.strip()):
        abort(400)
    try:
        value = float(value)
    except ValueError:
        abort(400)
    compr = data.get('compr')
    if not compr:
        abort(400)

    company = User.objects.get_or_404(id=id, pj=True)
    # Arquivo
    filename = secure_filename(compr['fileName'])
    content = base64.b64decode(compr['data'])
    bcontent = BytesIO(content)
    newfile = File(
        user = current_user.id,
        timestamp = datetime.utcnow().timestamp(),
        name = filename,
        content_type = compr['fileType'],
    )
    newfile.file.put(bcontent, app='finance', filename=filename, content_type=compr['fileType'])
    newfile.save()
    # Criar Pagamento
    payment = Payment(
        user = company.id,
        func = current_user.id,
        compr = newfile.id,
        value = value,
        type = 'cred',
        timestamp = datetime.utcnow().timestamp(),
        confirmed = True,
    )
    payment.save()
    # Descrição - Comentário
    desc = data.get('desc')

    if desc and desc.strip():
        comment = Event(
            timestamp = datetime.utcnow().timestamp(),
            actor = current_user.id,
            action = 'comment',
            object = 'payment',
            target = {
                'id': str(payment.id),
                'comment': desc.strip(),
            },
        )
        comment.save()

    return {'result': 'ok'}

@bp.get('/company/file')
@login_required
@check_roles(['fin'])
def get_company_file():
    id = request.args.get('id')
    if not id or len(id) < 12:
        abort(400)
    result = Payment.objects.get_or_404(id=id)
    return send_file(
        result.compr.file.get(),
        mimetype=result.compr.file.content_type,
    )
