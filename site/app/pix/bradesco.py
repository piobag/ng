from os import getenv
import base64
from datetime import datetime, timedelta
import pytz
import requests
import json


URL = getenv('BRADESCO_URL')
KEY = getenv('BRADESCO_KEY')
BASE64 = base64.b64encode(f"{getenv('BRADESCO_CLIENTKEY')}:{getenv('BRADESCO_CLIENTSECRET')}".encode()).decode()
scope = 'cobv.read cobv.write cob.read cob.write pix.read pix.write webhook.read webhook.write'
cert = ('/flask/cert.crt', '/flask/cert.key')

dias_vencimento = 1

class Bradesco:
    """Comunica com a API Pix do Bradesco"""
    def __init__(self):
        self.get_token()
        # if not self.token:
        #     return {'error': 'Não foi possível gerar o token'}

    def get_token(self):
        try:
            response = requests.post(
                f'{URL}/oauth/token',
                data = {
                    'grant_type': 'client_credentials',
                    'scope': scope
                },
                headers = {
                    'Authorization': f'Basic {BASE64}',
                    'Content-type': 'application/x-www-form-urlencoded'
                },
                cert = cert
            )
            self.token = response.json().get('access_token')
        except Exception as e:
            print(e)
            

    def nova_cobranca(self, txid, cpf, nome, valor, msg):
        vencimento = datetime.now(pytz.timezone('America/Sao_Paulo')).date() + timedelta(days=dias_vencimento)
        response = requests.put(
            f'{URL}/v2/cobv-emv/{txid}',
            json = {
                'chave': KEY,
                'devedor': {'cpf': cpf, 'nome': nome},
                'valor': {'original': valor},
                "calendario": {
                    "dataDeVencimento": vencimento.isoformat(),
                    "validadeAposVencimento": 0 },
                'solicitacaoPagador': msg
            },
            headers = {'Authorization': f'Bearer {self.token}'},
            cert = cert
        )
        print(response.status_code)
        print(json.dumps(response.json(), indent=4))
        return response.json()

    def revisa_cobranca(self, txid):
        response = requests.patch(
            f'{URL}/v2/cobv/{txid}',
            json = {
                'status': 'REMOVIDA_PELO_USUARIO_RECEBEDOR'
            },
            headers = {'Authorization': f'Bearer {self.token}'},
            cert = cert
        )
        print(response.status_code)
        print(json.dumps(response.json(), indent=4))

    def ver_cobranca(self, txid):
        response = requests.get(
            f'{URL}/v2/cobv/{txid}',
            headers = {'Authorization': f'Bearer {self.token}'},
            cert = cert
        )
        print(response.status_code)
        print(json.dumps(response.json(), indent=4))

    def listar_cobrancas(self, days=2, page=0, per_page=10):

        # 'inicio': '2022-01-10T18:00:00.000Z',
        # 'fim': '2022-01-12T10:00:00.000Z',

        inicio = datetime.now(pytz.timezone('America/Sao_Paulo'))-timedelta(days=days)
        response = requests.get(
            f'{URL}/v2/cobv',
            params = {
                'inicio': str(inicio.isoformat())+'Z',
                'fim': str(datetime.now().isoformat())+'Z',
                'paginacao': {
                    'paginaAtual': page,
                    'itensPorPagina': per_page
                }
            },
            headers = {'Authorization': f'Bearer {self.token}'},
            cert = cert
        )
        print(response.status_code)
        print(json.dumps(response.json(), indent=4))
