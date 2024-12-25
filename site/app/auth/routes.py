import re
from os import getenv
from datetime import datetime
from importlib import import_module
import pytz

from flask import (
    redirect,
    url_for,
    request,
    render_template,
    session,
    current_app,
    abort )
from flask_login import login_user, logout_user, current_user, login_required
from flask_babel import _
from werkzeug.urls import url_parse
import jwt

from . import (
    bp,
    is_human,
    check_roles,
    get_roles,
    get_json,
    Role,
    RoleBind,
    notify,
)
from .cpfcnpj import verify_cpfcnpj
from .. import db
from ..base import User

tz = pytz.timezone('America/Sao_Paulo')


@bp.get('/')
def index():
    next = request.args.get('next', '/')
    if current_user.is_authenticated:
        return redirect(f'{url_for("base.index")}?next={next}')
    return render_template(
        'auth/auth.html',
        user=session.get('wrong_login'),
        next=next,
    )

@bp.post('/register')
@get_json
def register(data):
    if current_user.is_authenticated:
        return redirect(url_for('base.index'))    
    if not current_app.debug:
        token = data.get('token')
        ip = request.headers.get('X-Original-Forwarded-For', request.remote_addr)
        if not token or not is_human(token, ip):
            return {'error': _('Failed to validate reCAPTCHA, please reload the page')}, 400
    if not re.fullmatch(
        '^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*@(?:\w+\.)+[A-Za-z0-9]+$', data['email']):
        return {'error', _('Enter a valid email address')}, 400
    if data['pwd'] != data['pwd2']:
        return {'error': _('Passwords do not match')}, 400

    #! Validar Senha

    # Email
    email = data['email'].strip().lower()
    # if User.objects.filter(email=email).first():
    #     return {'error': _('Mail already registered, use another or reset password.')}, 400

    # CPF/CNPJ
    if not verify_cpfcnpj(data['cpf']):
        return {'error': 'CPF/CNPJ inválido.'}, 400
    cpf = re.sub('\D', '', data['cpf'])
    if User.objects.filter(cpfcnpj=cpf).first():
        return {'error': 'CPF já cadastrado no sistema.'}, 400

    user = User(
        name=data['name'].strip().title(),
        email=email,
        cpfcnpj=cpf,
        timestamp = datetime.utcnow().timestamp(),
        tel=re.sub('\D', '', data['tel']) if data.get('tel') else None,
    )
    user.set_pwd(data['pwd'])

    # Direct confirm Admins and Users from config 
    if email in current_app.config['MAIL_ADMIN'] or \
                                email in current_app.config['MAIL_USERS']:
       user.confirmed_at = datetime.utcnow().timestamp()
    # try:
    user.save()
    # except db.NotUniqueError as e:
    #     return {'error': _('ID already registered')}, 400
    # except Exception as e:
    #     # print(e)
    #     notify( _('Error saving to the database'), e)
    #     return {'error': _('Error saving to the database')}, 400
    if user.confirmed_at:
        return {'result': _('Email verified, you can now login.')}
    try:
        user.send_mail(confirm=True)
    except Exception as e:
        # print(e)
        notify( _('Error sending confirmation email'), e)
        return {'error': _('Error sending confirmation email')}, 400
    return {'result': _('Account registered, click on the confirmation link sent to your email')}

@bp.post('/login')
@get_json
def login(data):
    if current_user.is_authenticated:
        return redirect(url_for('base.index'))
    user_id = data.get('id')
    if not (user_id):
        abort(400)

    session['wrong_login'] = user_id
    if not current_app.debug:
        token = data.get('token')
        ip = request.headers.get('X-Original-Forwarded-For', request.remote_addr)
        if not token or not is_human(token, ip):
            return {'error': _('Failed to validate reCAPTCHA, please reload the page')}
    try:
        user = User.objects.get(cpfcnpj=re.sub('\D', '', user_id))
        # user = User.objects.get(email=data['email'].lower())
    except db.DoesNotExist:
        return {'error': _('Invalid id or password.')}
    if not user.password:
        return {
            'error': _('Invalid password, please request a password reset'),
            'open': 'restore',
            'email': user.email,
        }
    if not user.chk_pwd(data['pwd']):
        return {'error': _('Invalid id or password.')}, 400
    if not user.confirmed_at and \
                not (user.email in current_app.config['MAIL_ADMIN'] or \
                     user.email in current_app.config['MAIL_USERS']):
        return {'error': _('Mail not validated yet, check your spam box for the confirmation link or request a password reset to be verified')}
    if not user.active:
        return {'error': _('Account disabled, contact admin.')}, 400
    session.pop('wrong_login')
    login_user(user, remember=data['remember'])

    # ! Testar se redirect funciona pelo fetch

    next_page = request.args.get('next', '/')
    # if url_parse(next_page).netloc != '':
    #     next_page = '/'
    return {'result': next_page}

@bp.post('/restore')
@get_json
def restore(data):
    if current_user.is_authenticated:
        return redirect(url_for('base.index'))
    user_id = data.get('id')
    if not (user_id):
        abort(400)

    if not current_app.debug:
        token = data.get('token')
        ip = request.headers.get('X-Original-Forwarded-For', request.remote_addr)
        if not token or not is_human(token, ip):
            return {'error': _('Failed to validate reCAPTCHA, please reload the page')}
    try:
        user = User.objects.get(cpfcnpj=re.sub('\D', '', user_id))
    except db.DoesNotExist:
        return {'error': _('This email is not registered yet.')}
    if user.email in current_app.config['MAIL_ADMIN'] or \
                user.email in current_app.config['MAIL_USERS']:
        token = user.get_mail_token('reset_user')
        return redirect(url_for('auth.reset', token=token))
    # try:
    user.send_mail(reset=True)
    # except Exception as e:
    #     print(e)
    #     # notify('Erro enviando email de recuperaçao de senha', e)
    #     return {'error': _('Unable to send recovery email. Try again.')}
    return {'result': _('Check your mail for the instructions to reset your password')}

@bp.get('/confirm/<token>')
def confirm(token):
    try:
        data = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256'] )
    except jwt.ExpiredSignatureError as e:
        return render_template('landingpage.html', message=_('Expired Token. Confirm your email reseting password.'))
    except Exception as e:
        print(f'\n\nError:\n{e}\n\n')
        return render_template('landingpage.html', message=_('Invalid Token.'))
    user = User.objects.filter(cpfcnpj=data.get('confirm_user')).first()
    if user:
        if user.confirmed_at:
            return render_template('landingpage.html', message=_('User already confirmed.'))
        else:
            user.confirmed_at = datetime.utcnow().timestamp()
            user.save()
            # login_user(user, remember=False)
            return render_template('landingpage.html', message=_('User verified, you can now login.'))
    abort(404)

@bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token):
    try:
        data = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256'] )
    except jwt.ExpiredSignatureError as e:
        return render_template('landingpage.html', message=_('Expired Token. Request a new password change.'))

    user = User.objects.filter(cpfcnpj=data.get('reset_user')).first()
    if user:
        if request.method == 'GET':
            return render_template(
                'auth/reset.html',
                token=token )
        elif request.method == 'POST':
            data = request.get_json()
            if not current_app.debug:
                ip = request.headers.get('X-Original-Forwarded-For', request.remote_addr)
                token = data.get('token')
                if not token or not is_human(token, ip):
                    return {'error': _('Failed to validate reCAPTCHA, please reload the page')}
            if not user.confirmed_at:
                user.confirmed_at = datetime.utcnow().timestamp()


            # ! Validar senha
            if data.get('pwd') != data.get('pwd2'):
                return {'error': _('Passwords do not match')}
            if not data.get('pwd') or len(data['pwd']) < 8:
                return {'error': _('Password must be at least 8 characters long')}

            user.set_pwd(data['pwd'])
            user.save()
            # login_user(user, remember=False)
            return {'result': _('Your password has been changed.')}
    abort(404)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('base.index'))

@bp.get('/users')
@login_required
@check_roles(['settings'])
def get_users():
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 10, type=int)
    search = request.args.get('search')
    filter = request.args.get('filter')

    if filter:
        role = Role.objects.filter(name=filter).only('id').first()
        if not role:
            return {'error': 'Filtro inválido'}, 400
        filtered = RoleBind.objects.filter(role=role.id)
        total_filtered = filtered.count()
        # if total_filtered < start+length:
        list = [x.user for x in filtered[start:(start+length)]]
    else:
        if search:
            total_filtered = User.objects.search_text(search).count()
            list = User.objects.search_text(search).skip(start).limit(length)
        else:
            total_filtered = User.objects.count()
            list = User.objects.skip(start).limit(length)

    return {
        'result': [user.to_dict() for user in list],
        'total': total_filtered,
    }

# Get a User
@bp.get('/user')
@login_required
@get_roles
def get_user(roles):
    userid = request.args.get('id')
    if userid:
        if '@' in userid and (userid == str(current_user.email) or 'adm' in roles):
            user = User.objects.get_or_404(email=userid)
        elif userid == str(current_user.id) or 'adm' in roles:
            user = User.objects.get_or_404(id=userid)
        else:
            return {'error': 'Não permitido'}
        return {'result': user.to_dict()}

@bp.put('/user')
@get_roles
@get_json
def put_user(data, roles):
    id = data.get('id')
    cpfj = data.get('cpfcnpj')
    email = data.get('email').strip().lower()
    name = data.get('name')
    if not (id and cpfj and email and name):
        abort(400)
    if not (id == str(current_user.id) or 'adm' in roles):
        abort(403)
    if not (cpfj or 'adm' in roles):
        return {'error': 'CPF/CNPJ obrigatório.'}, 400
    if not re.fullmatch(
            '^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*@(?:\w+\.)+[A-Za-z0-9]+$', email):
        return {'error', _('Enter a valid email address')}, 400

    user = User.objects.get_or_404(id=id)
    user.name = name.strip().title()
    tel = re.sub('\D', '', data.get('tel'))
    if tel != user.tel:
        user.tel = tel
    if not user.cpfcnpj or 'adm' in roles:
        user.cpfcnpj = cpfj
    if 'adm' in roles:
        if user.email != email:
            if User.objects.filter(email=email).first():
                return {'error': _("Email already registered in another account") },400
            user.email = email
        groups = data.get('groups') or []
        for role in Role.objects():
            if role.name in groups:
                rb = RoleBind.objects(role=role.id, user=user.id).first()
                if not rb:
                    RoleBind(role=role.id, user=user.id).save()
            else:
                rb = RoleBind.objects(role=role.id, user=user.id).first()
                if rb:
                    rb.delete()
        if data.get('lunch'):
            user.lunch = data['lunch'] if data['lunch'] != '00:00' else None
        if data.get('admissao'):
            user.admissao = tz.localize(datetime.strptime(data['admissao'], "%Y-%m-%d")).astimezone(pytz.utc).timestamp()
    try:
        user.save()
        return {'result': 'ok'}
    except Exception as e:
        notify(_("Error saving profile"), e)
        return {'error': _("Error saving profile")}, 400

def check_id(uid):
    if verify_cpfcnpj(uid):
        user = User.objects.filter(cpfcnpj=uid).first()
        if user:
            return {'result': {
                'name': user.name,
                'email': user.email,
                'tel': user.tel if user.tel else '',
            }}
        else:
            return {'noresult': True}
    else:
        return {'error': _('Invalid CPF/CNPJ')}

@bp.get('/id') # Get User ID
@login_required
@check_roles(['ri', 'fin'])
def get_id():
    uid = request.args.get('id')
    email = request.args.get('email')
    if email and uid:
        if not re.fullmatch('^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*@(?:\w+\.)+[A-Za-z0-9]+$', email):
            return {'error': _('Invalid email address')}
        get_user = check_id(uid)
        result = get_user.get('result')
        if result:
            if result['email'] == email:
                return {'result': 'ok'}
            else:
                return {'error': 'ID cadastrado com outro email'}
        noresult = get_user.get('noresult')
        if noresult:
            user = User.objects.filter(email=email).first()
            if user:
                return {'conflict': {'name': user.name, 'cpfcnpj': user.cpfcnpj}}
            else:
                return {'result': 'ok'}
        if get_user.get('error'):
            return get_user
    elif uid:
        return check_id(uid)
    abort(404)

