import re
from datetime import datetime
import pytz
from os import path

import jwt
from werkzeug.utils import secure_filename
from flask import render_template, request, current_app, abort, send_file
from flask_login import current_user, login_required
from flask_babel import _
from mongoengine.queryset.visitor import Q

from . import bp, Devol
from ..attend import Attend, Nature, Service
from ..finance import Payment, Account
from ..auth import get_roles, check_roles, get_json, notify
from ..auth.cpfcnpj import verify_cpfcnpj
from ..base import User, Event
from ..itm import Intimacao

tz = pytz.timezone('America/Sao_Paulo')

def get_attend_info(id):
    if isinstance(id, str):
        a = Attend.objects.get_or_404(id=id)
    else:
        a = Attend.objects.get_or_404(id=id.id)
    attend = {
        'id': str(a.id),

        'name': a.user.name,
        'cpf': a.user.cpfcnpj,
        'end': a.end,
        'email': a.user.email,

        'saldo': 0.0,
        'paid': 0.0,
        'to_pay': 0.0,
        'total': 0.0,
    }
    # Pagamentos confirmados no atendimento
    for p in Payment.objects.filter(attend=a.id, confirmed__ne=None):
        attend['paid'] += float(p.value)
    # Serviços executados no atendimento
    for s in Service.objects(attend=p.attend):
        attend['total'] += s.total
        attend['to_pay'] += s.paid
    # Uso de Saldo
    saldo_usado = attend['to_pay'] - attend['paid']
    if saldo_usado > 0:
        attend['paid'] += saldo_usado
    return attend


@bp.get('/')
@login_required
@check_roles(['fin'])
@get_roles
def index(roles):
    fromdate = tz.localize(datetime.strptime(f'{request.args.get("from", str(datetime.now(tz).date()))} 00', '%Y-%m-%d %H')).astimezone(pytz.utc).timestamp()
    enddate = tz.localize(datetime.strptime(f'{request.args.get("end", str(datetime.now(tz).date()))} 23:59:59', '%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc).timestamp()
    if enddate and not fromdate:
        return {'error': 'Selecione a data inicial.'}, 400

    users = {}
    total_payments = {}
    # total_attends =  []

    filter = request.args.get('filter')
    if filter:
        payments = Payment.objects.filter(confirmed__ne=None, confirmed__gt=fromdate, confirmed__lt=enddate, type=filter)
    else:
        payments = Payment.objects.filter(confirmed__ne=None, confirmed__gt=fromdate, confirmed__lt=enddate)
    # Buscando por pagamentos com func id
    for p in payments:
        uid = str(p.func.id)
        if not users.get(uid):
            users[uid] = {
                'name': str(p.func.name),
                'attends': {},
                'itms': {},
                'payments': {},
                'services': [],
            }
        # Attend
        if p.attend:
            # Adicionar o atendimento na lista do usuário
            if users[uid]['attends'].get(str(p.attend.id)):
                users[uid]['attends'][str(p.attend.id)]['paid'] += float(p.value)
            else:
                users[uid]['attends'][str(p.attend.id)] = {
                    'id': str(p.attend.id),
                    'name': p.attend.user.name,
                    'cpf': p.attend.user.cpfcnpj,
                    'end': p.attend.end,
                    'email': p.attend.user.email,

                    'paid': float(p.value),
                }

            # Total User
            if users[uid]['payments'].get(p.type):
                users[uid]['payments'][p.type] += p.value
            else:
                users[uid]['payments'][p.type] = p.value

            # Total Payments
            if total_payments.get(p.type):
                total_payments[p.type] += p.value
            else:
                total_payments[p.type] = p.value

        # Itm
        elif p.intimacao:
            # Adicionar intimação na lista do usuário
            if users[uid]['itms'].get(str(p.intimacao.id)):
                users[uid]['itms'][str(p.intimacao.id)]['paid'] += float(p.value)
            else:
                users[uid]['itms'][str(p.intimacao.id)] = {
                    'id': str(p.intimacao.id),
                    'start': p.intimacao.timestamp,
                    'itm': p.intimacao.cod,

                    'services': [x.to_dict() for x in Service.objects(intimacao=p.intimacao.id)],
                    'paid': float(p.value),
                    'orcado': 0.0,
                }
            typename = 'onr_Pagos'
            # User payments
            if users[uid]['payments'].get(typename):
                users[uid]['payments'][typename] += p.value
            else:
                users[uid]['payments'][typename] = p.value
            # Total payments
            typename = 'onr_Pagos'
            if total_payments.get(typename):
                total_payments[typename] += p.value
            else:
                total_payments[typename] = p.value

        # for s in Service.objects(attend=a):
        #     attend['total'] += s.total
        #     attend['to_pay'] += s.paid

        # # Uso de Saldo
        # saldo_usado = attend['to_pay'] - attend['paid']
        # if saldo_usado > 0:
        #     attend['paid'] += saldo_usado
        #     if total_payments.get('cred'):
        #         total_payments['cred'] += saldo_usado
        #     else:
        #         total_payments['cred'] = saldo_usado
        #     if users[uid]['payments'].get('cred'):
        #         users[uid]['payments']['cred'] += saldo_usado
        #     else:
        #         users[uid]['payments']['cred'] = saldo_usado

    # # Protocolos confirmados
    # for e in Event.objects.filter(action='pay', object='service',
    #                               actor=current_user.id,
    #                               timestamp__gt=fromdate, timestamp__lt=enddate):

    #     if total_payments.get('prot'):
    #         total_payments['prot'] += e.target['paying']
    #     else:
    #         total_payments['prot'] = e.target['paying']
    #     if users[uid]['payments'].get('prot'):
    #         users[uid]['payments']['prot'] += e.target['paying']
    #     else:
    #         users[uid]['payments']['prot'] = e.target['paying']


    ### Intimações Orçadas
    # for p in Payment.objects.filter(intimacao__ne=None, confirmed=None, timestamp__gt=fromdate, timestamp__lt=enddate):
    if not filter or filter == 'onro':
        for i in Intimacao.objects(orcado__gt=fromdate, orcado__lt=enddate):
            uid = str(i.func.id)
            if not users.get(uid):
                users[uid] = {
                    'name': i.func.name,
                    'attends': {},
                    'itms': {},
                    'payments': {},
                    'services': [],
                }

            orcado = 0.0
            for p in Payment.objects.filter(intimacao=i).limit(2).only('value'):
                orcado += p.value

            if users[uid]['itms'].get(str(i.id)):
                users[uid]['itms'][str(i.id)]['orcado'] += orcado
            else:
                users[uid]['itms'][str(i.id)] = {
                    'id': str(i.id),
                    'start': i.timestamp,
                    'itm': i.cod,

                    'services': [x.to_dict() for x in Service.objects(intimacao=i.id)],
                    'paid': 0.0,
                    'orcado': orcado,
                }

            typename = 'onro'
            # User payments
            if users[uid]['payments'].get(typename):
                users[uid]['payments'][typename] += orcado
            else:
                users[uid]['payments'][typename] = orcado
            # Total payments
            if total_payments.get(typename):
                total_payments[typename] += orcado
            else:
                total_payments[typename] = orcado

    ### Intimações Serviços Criados
    if not filter or filter == 'onr_Serviços':
        for event in Event.objects(timestamp__gt=fromdate, timestamp__lt=enddate, action='create', object='service', target__itm__ne=None):
            i = Intimacao.objects.filter(id=event.target['itm']).first()
            if not i:
                print(event.target)
                print(Service.objects.get(id='6468e85c42d99380c9948ee5').to_dict())

                notify('Apagando evento de intimação inexistente', f'Service {str(event.target["id"])}')
                # event.delete()
                continue
            uid = str(event.actor.id)
            if not users.get(uid):
                users[uid] = {
                    'name': event.actor.name,
                    'attends': {},
                    'itms': {},
                    'payments': {},
                    'services': [],
                }
            users[uid]['services'].append({
                'id': str(i.id),
                'date': event.target['date'],
                'type': event.target['type'],
                'nature': event.target['nature'],
                'prot': event.target['prot'],
                'paid': event.target['paid'],
            })

            typename = 'onr_Serviços'
            if total_payments.get(typename):
                total_payments[typename] += event.target['paid']
            else:
                total_payments[typename] = event.target['paid']
            # User payments
            if users[uid]['payments'].get(typename):
                users[uid]['payments'][typename] += event.target['paid']
            else:
                users[uid]['payments'][typename] = event.target['paid']

        ### Intimações Serviços Pagos
        for event in Event.objects(timestamp__gt=fromdate, timestamp__lt=enddate, action='pay', object='service', target__itm__ne=None):
            i = Intimacao.objects.filter(id=event.target['itm']).first()
            if not i:
                print(event.target)
                print(Service.objects.get(id='6468e85c42d99380c9948ee5').to_dict())

                notify('Apagando evento de intimação inexistente', f'Service {str(event.target["id"])}')
                # event.delete()
                continue
            uid = str(event.actor.id)
            if not users.get(uid):
                users[uid] = {
                    'name': event.actor.name,
                    'attends': {},
                    'itms': {},
                    'payments': {},
                    'services': [],
                }
            users[uid]['services'].append({
                'id': str(i.id),
                'date': event.target['date'],
                'type': event.target['type'],
                'nature': event.target['nature'],
                'prot': event.target['prot'],
                'paid': event.target['paid'],
            })

            typename = 'onr_Serviços'
            if total_payments.get(typename):
                total_payments[typename] += event.target['total'] - event.target['paid']
            else:
                total_payments[typename] = event.target['total'] - event.target['paid']
            # User payments
            if users[uid]['payments'].get(typename):
                users[uid]['payments'][typename] += event.target['total'] - event.target['paid']
            else:
                users[uid]['payments'][typename] = event.target['total'] - event.target['paid']

    return {'result': {
        'total_payments': total_payments,
        'users': users,
    }}

@bp.put('/payment-attend') # Confirm Attend Payment
@login_required
@check_roles(['attend'])
@get_json
def put_payment_attend(data):
    id = data.get('id')
    if not (id and len(id) == 24):
        abort(400)
    payment = Payment.objects.get_or_404(id=id)
    action = data.get('action')
    match action:
        case 'confirm':
            if payment.confirmed:
                return {'error': 'Payment already confirmed'}
            event = Event(
                timestamp = datetime.utcnow().timestamp(),
                actor = current_user.id,
                action = 'confirm',
                object = 'payment',
                target = payment.to_event(),
            )
            payment.confirmed = datetime.utcnow().timestamp()

            if payment.func != current_user.id:
                print(f'func diferente: {payment.func} / {current_user.id}')
                payment.func = current_user.id

            payment.save()
            event.save()
            return {'result': 'ok'}
        case _:
            abort(400)
    abort(400)

@bp.delete('/payment-attend') # Delete Attend Payment
@login_required
@check_roles(['fin'])
@get_json
def del_payment_attend(data):
    id = data.get('id')
    attend = data.get('attend')
    if not (id and len(id) == 24 and attend):
        abort(400)
    attend = Attend.objects.get_or_404(id=attend)
    payment = Payment.objects.get_or_404(id=id, attend=attend.id)
    try:
        event = Event(
            timestamp = datetime.utcnow().timestamp(),
            actor = current_user.id,
            action = 'delete',
            object = 'payment',
            target = payment.to_event(),
        )
        payment.delete_all()
        event.save()

        print('evento de delete')
        print(event.to_dict())
        
        return {'result': 'ok'}
    except Exception as e:
        msg = _('Error saving to database')
        notify(msg, e)
        return {'error': msg}, 400

@bp.post('payment') # New Itm Payment
@login_required
@check_roles(['itm'])
@get_json
def post_payment(data):
    id = data.get('id')
    value = data.get('value')
    if not (id and value):
        return {'error': 'Pass itm ID in "id" key'}
    itm = Intimacao.objects.get_or_404(id=id)
    payment = Payment(
        func=current_user.id,
        intimacao=itm.id,
        timestamp = datetime.utcnow().timestamp(),
        type = 'onr',
        value = value,
    )
    payment.save()

    event = Event(
        timestamp = datetime.utcnow().timestamp(),
        actor = current_user.id,
        action = 'create',
        object = 'payment',
        target = itm.to_list(),
    )
    event.save()
    return {'result': 'ok'}

@bp.get('/devols')
@login_required
@check_roles(['fin'])
def devols():
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 5, type=int)
    search = request.args.get('search')
    filter = request.args.get('filter')

    if filter:
        if filter == 'waiting':
            total_filtered = Devol.objects(choice=None).count()
            list = Devol.objects(choice=None).skip(start).limit(length).order_by('-timestamp')
        elif filter == 'finished':
            total_filtered = Devol.objects(paid=True).count()
            list = Devol.objects(paid=True).skip(start).limit(length).order_by('-timestamp')
        elif filter == 'pending':
            total_filtered = Devol.objects(Q(choice__ne=None) & Q(choice__ne='reprot'), paid=False).count()
            list = Devol.objects(Q(choice__ne=None) & Q(choice__ne='reprot'), paid=False).skip(start).limit(length)
        else:
            total_filtered = Devol.objects(choice=filter, paid=False).count()
            list = Devol.objects(choice=filter, paid=False).skip(start).limit(length)
    elif search:
        total_filtered = Devol.objects.search_text(search).count()
        list = Devol.objects.search_text(search).skip(start).limit(length)
    else:
        total_filtered = Devol.objects(paid=False, choice__ne=None).count()
        list = Devol.objects(paid=False, choice__ne=None).skip(start).limit(length)

    return {
        'result': 1,
        'list': [x.to_dict() for x in list],
        'total': total_filtered,
    }

@bp.post('/devol')
@login_required
@check_roles(['fin'])
@get_json
def post_devol(data):
    email = data['email'].strip().lower()
    if not re.fullmatch('^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*@(?:\w+\.)+[A-Za-z0-9]+$', email):
        return {'error': _('Enter a valid email address')}, 400
    cpf = re.sub('\D', '', data['cpf'])
    if not verify_cpfcnpj(cpf):
        return {'error': _('Invalid CPF')}, 400
    name = data['name'].strip().title()
    tel = re.sub('\D', '', data['tel'])
    user = User.objects.filter(cpfcnpj=cpf).first()
    if not user:
        # user = User.objects.filter(email=email).first()
        # if user:
        #     if user.cpfcnpj:
        #         notify('Conflito no new User devol', f'Email cadastrado em outra conta com o CPF {user.cpfcnpj}')
        #         return {'error': f'Email cadastrado em outra conta com o CPF {user.cpfcnpj}'}, 400
        #     user.cpfcnpj = cpf
        #     user.name = name
        #     user.tel = tel
        #     user.save()
        # else:
        if len(cpf) > 11:
            pj = True
        else:
            pj = False
        user = User(
            cpfcnpj=cpf,
            pj=pj,
            name=name,
            email=email,
            tel=tel,
        )
        user.save()
    prot = data['prot'].strip().upper()
    service = Service.objects.filter(prot=prot).first()
    if not service:
        nature = Nature.objects.filter(id=data['nature']).first()
        if not nature:
            return {'error': 'Natureza inválida'}, 400
        service = Service(
            timestamp=datetime.utcnow().timestamp(),
            prot=prot,
            type='prot',
            nature=nature.id,
        )
        try:
            service.save()
        except Exception as e:
            msg = f"{_('Error saving to database')}: new service"
            notify(msg, e)
            return {'error': msg}, 400

    devol = Devol(
        func = current_user.id,
        user = user.id,
        service = service.id,
        value = float(data['value']),
        timestamp = datetime.utcnow().timestamp(),
    )
    try:
        devol.save()
    except Exception as e:
        msg = f"{_('Error saving to database')}: devol"
        notify(msg, e)
        return {'error': msg}, 400
    try:
        devol.send_mail()
        return {'result': 'Devolução registrada.'}
    except Exception as e:
        notify(f"{_('Error sending email to')} {data['email']}", e)
        devol.delete()
        return {'error': f'Falha ao enviar o email para {data["email"]}, tente novamente.'}

@bp.get('/devol')
@login_required
@check_roles(['fin'])
def get_devol():
    id = request.args.get('id')
    if not id or len(id) < 12:
        abort(400)
    return {'result': Devol.objects.get_or_404(id=id).to_info()}

@bp.put('/devol')
@login_required
@check_roles(['fin'])
@get_json
def put_devol(data):
    # transf = data.get('transf')
    # if transf:
    #     devol = Devol.objects.get_or_404(id=transf)
    #     return {'result': devol}
    resend = data.get('resend')
    if resend:
        devol = Devol.objects.get_or_404(id=resend)
        if devol.choice:
            return {'error': 'Devolução já respondida'}, 400
        try:
            devol.send_mail()
            return {'result': 'Email reenviado.'}
        except Exception as e:
            notify('Falha ao reenviar email', e)
            return {'error': 'Falha ao reenviar o email, tente novamente.'}, 400

    retireok = data.get('retireok')
    if retireok:
        devol = Devol.objects.get_or_404(id=retireok)
        if not (devol.choice and devol.choice == 'retire' and not devol.paid):
            return {'result': 'Devolução inválida para esta ação.'}, 400
        devol.send_mail(retireok=True)
        devol.paid = True
        devol.save()
        return {'result': 'Aviso enviado para o cliente.'}

    abort(400)

@bp.route('/devol/<token>', methods=['GET', 'POST'])
def devol_resp(token):
    try:
        data_token = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
    except Exception as e:
        notify('Erro decodificando token', e)
        abort(400)
    if not data_token:
        abort(404)
    id = data_token.get('devol')
    if id:
        devol = Devol.objects.get_or_404(id=id)
    else:
        id = data_token.get('prot')
        devol = Devol.objects.get_or_404(service=Service.objects.get_or_404(prot=id))
    if devol.choice:
        return render_template('landingpage.html', message='Os dados para esta devolução já foram informados.')
    if request.method == 'GET':
        return render_template(
            'landingpage.html',
            token=token,
            devol=devol.to_dict(),
            devolresp=True,
        )
    data = request.get_json()
    if not (data and data.get('choice')):
        abort(400)
    devol.choice = data['choice']
    if data['choice'] == 'transf':
        banco = data['banco'].strip().title()
        agencia = data['agencia'].strip().lower()
        conta = data['conta'].strip().lower()
        if len(banco) < 3:
            return {'error': _("Please enter the bank name correctly")}, 400
        if len(agencia) < 4:
            return {'error': _("Please enter the agency number correctly")}, 400
        if len(conta) < 5:
            return {'error': _("Please enter the account number correctly")}, 400
        account = Account(
            user = devol.user,
            banco = banco,
            tipo = data['tipo'],
            agencia = agencia,
            conta = conta,
        )
        account.save()
        devol.account = account.id
        devol.check = datetime.utcnow().timestamp()
    elif data['choice'] == 'retire':
        devol.check = datetime.utcnow().timestamp()
    elif data['choice'] == 'reprot':
        pass
    else:
        abort(400)
    try:
        devol.save()
        return {'result': 'Opção registrada.'}
    except Exception as e:
        notify(_('Error saving to database'), e)
        return {'error': _('Error saving to database')}, 400

@bp.get('/devol/file')
@login_required
@get_roles
def get_devol_file(roles):
    id = request.args.get('id')
    if not id or len(id) < 12:
        abort(400)
    devol = Devol.objects.get_or_404(id=id)
    if not ('fin' in roles or current_user.id == devol.user.id):
        abort(403)
    if devol.transf:
        return send_file(
            devol.transf.get(),
            mimetype=devol.transf.content_type,
        )
    elif devol.retire:
        return send_file(
            devol.retire.get(),
            mimetype=devol.retire.content_type,
        )
    else:
        abort(400)

@bp.post('/devol/file')
@login_required
@check_roles(['fin'])
def post_devol_file():
    id = request.form.get('id')
    if not id or len(id) < 12:
        abort(400)
    if request.files['devol_file'].filename == '':
        return {'error': 'Nenhum arquivo recebido'}, 400
    filename = secure_filename(request.files['devol_file'].filename)
    if not path.splitext(filename)[1].lower() in ['.jpg', '.jpeg', '.png', '.gif']:
        return {'error': 'Tipo de arquivo inválido'}, 400
    devol = Devol.objects.get_or_404(id=id)
    if devol.choice == 'transf':
        devol.transf.put(request.files['devol_file'].stream, content_type=request.files['devol_file'].content_type)
    elif devol.choice == 'retire':
        devol.retire.put(request.files['devol_file'].stream, content_type=request.files['devol_file'].content_type)
    else:
        abort(400)
    devol.paid = True
    try:
        devol.save()
        try:
            devol.send_mail(transfok=True)
        except Exception as e:
            notify(f'Erro enviando email Devol transfok {str(devol.id)}', e)
            return {'error': 'Erro enviando email. Devolução salva.'}
        return {'result': 'ok'}


    except Exception as e:
        notify(_('Error saving to database'), e)
        return {'error': _('Error saving to database')}, 400
