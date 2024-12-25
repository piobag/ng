import secrets
from os import getenv
from datetime import timedelta

class Config(object):
    TITLE = getenv('TITLE')
    SECRET_KEY = getenv('SECRET_KEY') or secrets.token_urlsafe()

    MAIL_ADMIN = getenv('MAIL_ADMIN', '').split(',')
    MAIL_USERS = getenv('MAIL_USERS', '').split(',')
    MAIL_CONTACT = getenv('MAIL_CONTACT', '').split(',')
    MAIL_DEFAULT_SENDER = f"{getenv('TITLE')} - Não responda <{getenv('MAIL_USERNAME')}>"

    DOMAIN = getenv('DOMAIN')

    SESSION_COOKIE_DOMAIN = f".{DOMAIN}"
    REMEMBER_COOKIE_DOMAIN = f".{DOMAIN}"

    LANGUAGES = ['en', 'en_US', 'pt', 'pt_BR', 'es', 'es_ES']

    RECAPTCHA_SITEKEY = getenv('RECAPTCHA_SITEKEY')
    RECAPTCHA_SECRETKEY = getenv('RECAPTCHA_SECRETKEY')

    MONGODB_SETTINGS = {'host': getenv('MONGO_URI'), 'connect': False}

    MAIL_SERVER = getenv('MAIL_SERVER')
    MAIL_USERNAME = getenv('MAIL_USERNAME')
    MAIL_PASSWORD = getenv('MAIL_PASSWORD')
    MAIL_PORT = int(getenv('MAIL_PORT') or 587)
    MAIL_USE_TLS = getenv('MAIL_USE_TLS') or True

    MAX_CONTENT_LENGTH = 64 * 1024 * 1024

    OPEN = '09:00'
    CLOSE = '17:00'
    FREQ = '5min'

    LOCAL = ('GO', 'Cidade Ocidental')

    SERVENTIA = {
        'LOCAL' : ('GO', 'Cidade Ocidental'),
        'OPEN' : '09:00',
        'CLOSE' : '17:00',
        'HOLD' : 'Márcio Silva Fernandes',
        'DESC' : 'Cartório de Registro de Imóveis de Cidade Ocidental-GO',
        'TYPE' : 'Registrador',
        'CERT_CRT' : '/certs/cert.crt',
        'CERT_KEY' : '/certs/cert.key',
        'CERT_CA' : '/certs/cert.ca',
        # 'CERT_PWD' : getenv('CERT_PWD'),
    }

    EST_CIVIS = {
        'sol': { 'name': 'Solteiro(a)', 'text': 'solteir_'},
        'cas': { 'name': 'Casado(a)', 'text': 'casad_'},
        'sep': { 'name': 'Separado(a)', 'text': 'separad_'},
        'div': { 'name': 'Divorciado(a)', 'text': 'divorciad_'},
        'viu': { 'name': 'Viúvo(a)', 'text': 'viúv_'},
        'uni': { 'name': 'União Estável', 'text': 'em união estável'},
    }

    BOOKING_SERVICES =  {
        'ri': {
            'name': 'Entrada em Protocolos',
            'mins': 15,
            'has_value': True },
        'pc': {
            'name': 'Pedido de Certidão',
            'mins': 10,
            'has_value': True },
        'ep': {
            'name': 'Retirada de Protocolos',
            'mins': 10,
            'has_value': False },
        'ec': {
            'name': 'Retirada de Certidões',
            'mins': 10,
            'has_value': False },
        'ex': {
            'name': 'Exigências',
            'mins': 20,
            'has_value': False }
    }

    SERVICES = {
        'prot': {'name': 'Protocolo'},
        'cert': {'name': 'Certidão'},
        'repr': {'name': 'Re-Protocolo'},
        'ec': {'name': 'Exame/Cálculo', 'nopay': True},
    }

    PAYMENTS = {
        'cc': {'name': 'Crédito'},
        'cd': {'name': 'Débito'},
        'din': {'name': 'Dinheiro'},
        'pix': {'name': 'Pix', 'hide': True},
        'ps': {'name': 'Pix Sicoob'},
        'pb': {'name': 'Pix Bradesco'},
        'tra': {'name': 'Transferência'},
        'bol': {'name': 'Boleto', 'pending': True},
        'onro': {'name': 'Onr Orçado', 'pending': True},
        'onr': {'name': 'Onr'},
        'lc': {'name': 'Linha Crédito'},
        'cred': {'name': 'Credenciamento', 'hide': True},
        'prot': {'name': 'Protocolo', 'hide': True},
    }

    POPUP_ROUTES = {
        'index': 'Home',
        'bookingnew': 'Agendamento',
        'certidao': 'Certidão',
        'consulta': 'Consulta'
    }

    AUTH_ROLES = {
        'adm': 'Administrador',
        'audit': 'Auditoria',
        'settings': 'Ajustes',
        'ti': 'TI',
        'ng': 'Colaborador',
        'fin': 'Financeiro',
        'itm': 'Intimação',
        'itm-sign': 'ITM - Assinador',
        'ri': 'Atendente',
        'digitizer': 'Digitalizador',
        'digitizer-signer': 'Assinador Digit'
    }

    CREDORES = [
        {
            'name': 'CAIXA ECONÔMICA FEDERAL',
            'cnpj': '00.360.305/0001-04',
            'sede': 'SETOR BANCÁRIO SUL, QUADRA 4, LOTES 3/4, BRASÍLIA - DF',
        },
        {
            'name': 'BANCO DO BRASIL S/A',
            'cnpj': '00.000.000/0001-91',
            'sede': 'SBS Quadra 01 Lote 32 Bloco C - Ed. Sede III, 24º andar, Setor Bancário Sul, Brasília/DF',
        },
        {
            'name': 'BANCO SANTANDER (BRASIL) S.A.',
            'cnpj': '90.400.888/0001-42',
            'sede': 'Avenida Presidente Juscelino Kubitschek, nº 2235 e 2041, São Paulo-SP',
        },
    ]

