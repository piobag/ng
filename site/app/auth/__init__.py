from time import time, sleep
from datetime import timedelta
from functools import wraps
import requests
import pytz

from flask import Blueprint, current_app, render_template, request, abort, session
from flask_login import UserMixin, current_user
from flask_mail import Message
from flask_babel import _
from mongoengine.queryset.visitor import Q
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from .. import db, mail, login

tz = pytz.timezone('America/Sao_Paulo')

bp = Blueprint('auth', __name__)

class User(db.Document, UserMixin):
    cpfcnpj = db.StringField(max_length=14, unique=True, required=True)
    email = db.EmailField(max_length=64)
    name = db.StringField(max_length=128)
    tel = db.StringField(max_length=20)
    pj = db.BooleanField(default=False)

    password = db.StringField(max_length=128)
    active = db.BooleanField(default=True)
    last_check = db.FloatField()
    confirmed_at = db.FloatField()
    timestamp = db.FloatField()
    meta = {'allow_inheritance': True,
            'strict': False,
            'indexes': [{
                'fields': ['$name', '$email', '$cpfcnpj'],
                'weights': {'name': 3, 'email': 2, 'cpfcnpj': 2} }]
    }
    def __repr__(self):
        return '<User {}>'.format(self.name)
    def to_list(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'cpfcnpj': self.cpfcnpj,
            'tel': self.tel if self.tel else '',
            'email': self.email,
        }
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'cpfcnpj': self.cpfcnpj,
            'roles': [x.role.name for x in RoleBind.objects(user=self.id).only('role')],
            'tel': self.tel if self.tel else '',
            'email': self.email,
        }
    def set_pwd(self, password):
        self.password = generate_password_hash(password)
    def chk_pwd(self, password):
        if not self.password:
            return False
        return check_password_hash(self.password, password)
    def get_mail_token(self, title, expires_in=3600):
        token = jwt.encode(
            {title: self.cpfcnpj, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256',
        )
        return token
    def send_mail(self, confirm=False, reset=False):
        if confirm:
            title = (_('Registration confirmation'), 'confirm_user')
        elif reset:
            title = (_('Reset your password'), 'reset_user')
        else:
            return False
        token = self.get_mail_token(title[1])
        # token = jwt.encode(
        #     {title[1]: self.cpfcnpj, 'exp': time() + 14400},
        #     current_app.config['SECRET_KEY'],
        #     algorithm='HS256')
        msg = Message(
            title[0],
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[self.email]
        )
        msg.body = render_template(
            'auth/mail.txt',
            title=title[0],
            token=token,
            auth=True,
            confirm=confirm,
            reset=reset,
            user=' '.join([x.capitalize() for x in self.name.split(' ')])
        )
        msg.html = render_template(
            'auth/mail.html',
            title=title[0],
            token=token,
            auth=True,
            confirm=confirm,
            reset=reset,
            user=' '.join([x.capitalize() for x in self.name.split(' ')])
        )
        try:
            mail.send(msg)
        except Exception as e:
            try:
                notify(f'Exception sending mail', e)
            except Exception as e:
                pass
            sleep(5)
            mail.send(msg)

class Role(db.Document):
    name = db.StringField(required=True, unique=True)
    text = db.StringField(required=True)
    parent = db.ReferenceField('Role')
    desc = db.StringField()

class RoleBind(db.Document):
    user = db.ReferenceField(User, required=True)
    role = db.ReferenceField(Role, required=True)

@login.user_loader
def load_user(id):
    try:
        return User.objects.get(id=id)
    except db.DoesNotExist:
        return None

def get_json(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        data = request.get_json()
        if data and request.content_type == 'application/json':
            return f(data, *args, **kwargs)
        abort(400)
    return wrapped

def get_roles(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if current_user.is_authenticated:
            roles = [x.role.name for x in RoleBind.objects(user=current_user.id).only('role')]
            if not 'adm' in roles and current_user.email in current_app.config['MAIL_ADMIN']:
                roles.append('adm')
        else:
            roles = []
        return f(roles, *args, **kwargs)
    return wrapped

def check_roles(roles):
    def inner_decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):

            # # Restringir acesso ao horário comercial
            # if not 'adm' in roles:
            #     if str(datetime.now(tz).time()).split(':')[0] > "19" or str(datetime.now(tz).time()).split(':')[0] < "07":
            #        abort(403)

            for role in roles:
                if role == 'adm' and current_user.email in current_app.config['MAIL_ADMIN']:
                    return f(*args, **kwargs)
                r = Role.objects(name=role).only('id').first()
                if r:
                    rb = RoleBind.objects(Q(user=current_user.id) & Q(role=r.id))
                    if rb:
                        return f(*args, **kwargs)
            abort(403)
        return wrapped
    return inner_decorator

def notify(title, text):
    if current_app.debug:
        print(f'\n\n{title}\n{text}\n\n')
    else:
        msg = Message('Notify Event',
                    sender=current_app.config['MAIL_DEFAULT_SENDER'],
                    recipients=current_app.config['MAIL_ADMIN'])
        if current_user.is_authenticated:
            title += f'\n - {_("User")}: {current_user.email}'
        title += f'\n - Agent: {str(request.user_agent)}'
        title += f"\n - IP: {request.headers.get('X-Original-Forwarded-For', request.remote_addr)}"
        title += f'\n\n{text}'
        msg.body = title
        mail.send(msg)

def is_human(token, ip):
    url = 'https://www.google.com/recaptcha/api/siteverify'
    payload = {
        'secret': current_app.config['RECAPTCHA_SECRETKEY'],
        'response': token,
        'remoteip': ip
    }
    r = requests.post(url, payload).json()
    if r.get('success') and r['score'] >= 0.6:
        return True
    return False

from . import routes
