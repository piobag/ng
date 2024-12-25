import jwt

from flask import (
    current_app,
    request,
    render_template,
    redirect,
    url_for,
    abort,
)
from flask_login import current_user, login_required
from flask_mail import Message
from flask_babel import _

from . import bp
from .. import mail
from ..popup import Popup
from ..auth import notify, get_roles, get_json
from ..finance import Devol
from ..itm import Credor
from ..attend import Service


# @bp.get('/tey')
# def tey():
#    from flask_login import login_user, logout_user
#    from app.auth import User
#    u = User.objects.get_or_404(email='ariadne.araujo@ng.digital')
#    logout_user()
#    login_user(u, remember=False)
#    return redirect(url_for('base.index'))


@bp.get('/dashboard')
@login_required
@get_roles
def dashboard(roles):
    credores = []
    visita = request.args.get('visita')
    if 'fin' in roles or 'itm' in roles:
        credores = [x.to_dict() for x in Credor.objects()]
    if len(roles) > 0:
        return render_template(
            'dashboard.html',
            roles=roles,
            visita=visita,
            credores=credores,
        )
    return redirect(url_for('base.index'))

@bp.get('/')
@get_roles
def index(roles):
    if ('adm' in roles or 'ng' in roles) and not request.args.get('home'):
        return redirect(url_for('base.dashboard'))
    popups = []
    if not current_app.debug:
        popups = Popup.objects.filter(active=True)
    service_docs = request.args.get('service_docs')
    if service_docs:
        try:
            data_token = jwt.decode(
                service_docs,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
        except jwt.ExpiredSignatureError as e:
            return render_template('landingpage.html', message='Token expirado.')
        except Exception as e:
            notify('Erro decodificando token', e)
            abort(400)
        if not data_token:
            abort(404)
        id = data_token.get('service')
        if not (id and len(id) == 24):
            abort(400)
        svc = Service.objects.get_or_404(id=id)
        entregue = True
        for d in Doc.objects(service=svc.id).only('entregue'):
            if not d.entregue:
                entregue = False
        if entregue:
            return render_template('landingpage.html', message='Serviço sem documento faltante.')
        return render_template(
            'landingpage.html',
            roles=roles,
            service_docs=svc.to_dict(),
        )
    if current_user.is_authenticated:
        return render_template(
            'landingpage.html',
            roles=roles,
            popups=popups,
            show=request.args.get('show') )
    else:
        return render_template(
            'landingpage.html',
            roles=roles,
            popups=popups,
            show=request.args.get('show') )

@bp.post('/')
@get_json
def contact(data):
    name = data['name']
    email = data['email']
    tel = data['tel']
    typeof = data['type']
    subject = data['subject']
    message = data['message']
    if not name or not email or not message:
        return {'error': _('Fill in all form fields')}, 400
    title = _('New Site Contact')
    msg = Message(
        title,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=current_app.config['MAIL_CONTACT']
    )
    msg.body =  render_template(
        'email.txt',
        title = title,
        contact = {
            'name': name,
            'email': email,
            'tel': tel,
            'type': typeof,
            'subject': subject,
            'message': message
        }
    )
    msg.html = render_template(
        'email.html',
        title = title,
        contact = {
            'name': name,
            'email': email,
            'tel': tel,
            'type': typeof,
            'subject': subject,
            'message': message
        }
    )
    try:
        mail.send(msg)
        return {'result': 'Mensagem enviada, responderemos em breve!'}
    except Exception as e:
        notify(f'Exception sending mail', e)
        return {'error': 'A mensagem não foi enviada, por favor tente novamente, pode ser preciso aguardar alguns minutos ou recarregar a página.'}, 400
        # sleep(5)
        # mail.send(msg)

@bp.get('/status')
@login_required
@get_roles
def status(roles):
    last = current_user.last_check or 0
    list = []
    if 'finance' in roles:
        for d in Devol.objects.filter(check__gt=last).only('id', 'choice'):
            list.append({'id': str(d.id), 'choice': d.choice})
    if 'itm' in roles:
        # itm 
        pass
    return {'result': list}
