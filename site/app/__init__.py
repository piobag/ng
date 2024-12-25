from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import Config
# CSRF
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()
# CORS
from flask_cors import CORS
cors = CORS(supports_credentials=True)
# Babel
from flask import Flask, request, current_app
from flask_babel import Babel, lazy_gettext as _l
babel = Babel() #locale_selector=get_locale)
# Login
from flask_login import LoginManager
login = LoginManager()
# MongoDB
from flask_mongoengine import MongoEngine
db = MongoEngine()
# Mail
from flask_mail import Mail
mail = Mail()
# Logging
import logging
from logging.handlers import SMTPHandler
from werkzeug.debug import DebuggedApplication
# Flask-Moment
from flask_moment import Moment
moment = Moment()


def create_app(config=Config):
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.config.from_object(config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
    csrf.init_app(app)
    cors.init_app(app)
    # Login
    login.login_view = 'auth.index'
    login.login_message = _l('Please login.')
    login.init_app(app)
    # MongoDB
    db.init_app(app)
    # Mail
    mail.init_app(app)
    # Logging
    secure = None
    if app.config['MAIL_USE_TLS']:
        secure = ()
    mail_handler = SMTPHandler(
        mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
        fromaddr=app.config['MAIL_DEFAULT_SENDER'],
        toaddrs=app.config['MAIL_ADMIN'],
        subject=f"{app.config['TITLE']} - Error!",
        credentials=(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']),
        secure=secure)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
    if app.debug:
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

    # CLI
    from .cli import register as cli
    cli(app)

    # Babel
    def get_locale():
        return request.accept_languages.best_match(current_app.config['LANGUAGES'])
    babel.init_app(app, locale_selector=get_locale)
    # babel = Babel(app)

    # Auth
    from .auth import bp as auth
    app.register_blueprint(auth, url_prefix='/auth')
    # Errors
    from .errors import bp as errors
    app.register_blueprint(errors)

    # Base
    from .base import bp as base
    app.register_blueprint(base)
    # Audit
    from .audit import bp as audit
    app.register_blueprint(audit, url_prefix='/audit')
    # Finance
    from .finance import bp as finance
    app.register_blueprint(finance, url_prefix='/finance')
    # Attend
    from .attend import bp as attend
    app.register_blueprint(attend, url_prefix='/attend')
    # Intimação
    from .itm import bp as itm
    app.register_blueprint(itm, url_prefix='/itm')
    # Booking
    from .booking import bp as booking
    app.register_blueprint(booking, url_prefix='/booking')
    # Popup
    from .popup import bp as popup
    app.register_blueprint(popup, url_prefix='/popup')
    # Ferias
    from .ferias import bp as ferias
    app.register_blueprint(ferias, url_prefix='/ferias')

    # FS
    from .fs import bp as fs
    app.register_blueprint(fs, url_prefix='/fs')

    # TI
    from .ti import bp as ti
    app.register_blueprint(ti, url_prefix='/ti')

    return app
