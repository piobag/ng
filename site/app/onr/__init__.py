from os import getenv
import base64
from datetime import datetime, timedelta
import pytz
import requests
import json

# URL = getenv('ONR_URL')
URL = 'http://hml.wsoficio.onr.org.br'

KEY = getenv('ONR_KEY')
ID = getenv('ONR_ID')
CPF = getenv('ONR_CPF')
EMAIL = getenv('ONR_EMAIL')

cert = ('/flask/cert.crt', '/flask/cert.key')
tokens = []

SUBJECTCN = 'CARTORIO DE REGISTRO DE IMOVEIS E ANEXOS:20155167000139'
ISSUERO = 'ICP-Brasil'
PUBLICKEY = '''-----BEGIN CERTIFICATE-----
MIIIGDCCBgCgAwIBAgIQbH1Va4+n0a8PVSahkoJOgzANBgkqhkiG9w0BAQsFADB4
MQswCQYDVQQGEwJCUjETMBEGA1UEChMKSUNQLUJyYXNpbDE2MDQGA1UECxMtU2Vj
cmV0YXJpYSBkYSBSZWNlaXRhIEZlZGVyYWwgZG8gQnJhc2lsIC0gUkZCMRwwGgYD
VQQDExNBQyBDZXJ0aXNpZ24gUkZCIEc1MB4XDTIxMDkyODEzNDYwMloXDTIyMDky
ODEzNDYwMlowggEKMQswCQYDVQQGEwJCUjETMBEGA1UECgwKSUNQLUJyYXNpbDEL
MAkGA1UECAwCR08xGTAXBgNVBAcMEENpZGFkZSBPY2lkZW50YWwxEzARBgNVBAsM
ClByZXNlbmNpYWwxFzAVBgNVBAsMDjAwNjc5MTYzMDAwMTQyMTYwNAYDVQQLDC1T
ZWNyZXRhcmlhIGRhIFJlY2VpdGEgRmVkZXJhbCBkbyBCcmFzaWwgLSBSRkIxFjAU
BgNVBAsMDVJGQiBlLUNOUEogQTExQDA+BgNVBAMMN0NBUlRPUklPIERFIFJFR0lT
VFJPIERFIElNT1ZFSVMgRSBBTkVYT1M6MjAxNTUxNjcwMDAxMzkwggEiMA0GCSqG
SIb3DQEBAQUAA4IBDwAwggEKAoIBAQCVqNW3Fq7nWmEDawFle50t+/3bYkYPYDfS
fSeQaR9vjy04kkKwSG2W2OdgeN8q3HG84+uEADoDL+51RnRfNhSO/tvL5CH6zI/s
rpllCWxve91TEbw5oWV0ZNg4yqQTA3A4+UdVcM5A+ka1zQ+kvEl11ec6sNkYOBWj
hZG3YLKKwF2hKi0xlpaKU1pT3pIR6cA2abUtO2J2o798L2PSs6ebnurmaqex992f
mlAwwUI3cul7/nu9qCDVzQX1R2xo1E1qaQP0laqPiDcWmIU8Z3xESXQkh6tYM7Qx
6660qVE0y+jY+/WehpFEasdv2Khr5r2TZlQg1zqBLxL6TQ1Ya9IhAgMBAAGjggMI
MIIDBDCBtwYDVR0RBIGvMIGsoD0GBWBMAQMEoDQEMjA0MTExOTcwNTI0MjQ4MDQx
NjgwMDAwMDAwMDAwMDAwMDAwMDAwMTA4NjE0MFNTUERGoCEGBWBMAQMCoBgEFk1B
UkNJTyBTSUxWQSBGRVJOQU5ERVOgGQYFYEwBAwOgEAQOMjAxNTUxNjcwMDAxMzmg
FwYFYEwBAwegDgQMNzAwMTI5NTc0NTA0gRRtYXJjaW9zZmVyQGdtYWlsLmNvbTAJ
BgNVHRMEAjAAMB8GA1UdIwQYMBaAFFN9f52+0WHQILran+OJpxNzWM1CMH8GA1Ud
IAR4MHYwdAYGYEwBAgEMMGowaAYIKwYBBQUHAgEWXGh0dHA6Ly9pY3AtYnJhc2ls
LmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8vZHBjL0FDX0NlcnRpc2lnbl9S
RkIvRFBDX0FDX0NlcnRpc2lnbl9SRkIucGRmMIG8BgNVHR8EgbQwgbEwV6BVoFOG
UWh0dHA6Ly9pY3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8v
bGNyL0FDQ2VydGlzaWduUkZCRzUvTGF0ZXN0Q1JMLmNybDBWoFSgUoZQaHR0cDov
L2ljcC1icmFzaWwub3V0cmFsY3IuY29tLmJyL3JlcG9zaXRvcmlvL2xjci9BQ0Nl
cnRpc2lnblJGQkc1L0xhdGVzdENSTC5jcmwwDgYDVR0PAQH/BAQDAgXgMB0GA1Ud
JQQWMBQGCCsGAQUFBwMCBggrBgEFBQcDBDCBrAYIKwYBBQUHAQEEgZ8wgZwwXwYI
KwYBBQUHMAKGU2h0dHA6Ly9pY3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIvcmVw
b3NpdG9yaW8vY2VydGlmaWNhZG9zL0FDX0NlcnRpc2lnbl9SRkJfRzUucDdjMDkG
CCsGAQUFBzABhi1odHRwOi8vb2NzcC1hYy1jZXJ0aXNpZ24tcmZiLmNlcnRpc2ln
bi5jb20uYnIwDQYJKoZIhvcNAQELBQADggIBAEmlwsbwbWrLPV7VLak8yVFmeiQ9
hsppLVTPJXBMfGQTGCfKreSnS8MIS3bhZgOUWRYfEDGsgMkfjlOx52D7Y579Tvs8
gKnnYllMg64mU8efGenrjSfM3M//UeehYOS6g/dGkQTV2jP/0BtKg5UJoR/gNq+s
nivLMOdKfGXFiPIFAzBcAmftfFiCh/wywKhi7/XlzmxGEMYK3At8LJvjxWsq55DK
XmmsWXIG0cQqj34obK7HJaA12zjE2+mebey6n5/gTZgMvV5shF4bNKej60Ft49Jg
yxqBiIXs2t8HRRYDCyyrPzC3FYJUt92giBZJEJt4dCfj9lWq3d3zNUeyZppaDR3r
Ug6zIcgnaUwr7Hl9stRwNEXjnlvLeV8clVYvoGF74LCrqyYD88Ce0y2+lSqVrZLD
0yalzlok3O1ldfGC2tRMKP8+yUaNDOXBdlp2X65M/5bbt1gPRatiP5mDew2xsufM
iQoDWB3nCxD68ayrCQa1hk29yW0N8VWudmtIYEIOUnODvlWXF9lotB1JjHW/hdUI
/WE2e+ivm28+043g0ShbHSW4LcqMTcomZcOVbledf60VC9Erp5+mIMq9tYRoGeCN
wRw6W6RA/vIMA5923+a27tMn9PvIC5B9D2i/9IzNnXD7VypRVgpeUuXDKYd7Il78
q3hdvLv0w2OI6Wut
-----END CERTIFICATE-----'''

SERIALNUMBER = '6c7d556b8fa7d1af0f5526a192824e83'
VALIDUNTIL = 'Sep 28 13:46:02 2022 GMT'


### Token
# - Gerado no momento da requisição
# - 5 tokens retornados por vez por padrão
# - Validade 5 dias

### Hash de autenticação
# - Combinação da chave + token.
# - Codificado no padrão SHA-1, codificação UTF-8.

def create_token():
    print('Creating Token')

    print(ID)
    print(CPF)
    body = f'''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <LoginUsuarioCertificado xmlns="http://tempuri.org/WSOficio">
      <oRequest>
        <SUBJECTCN>{SUBJECTCN}</SUBJECTCN>
        <ISSUERO>{ISSUERO}</ISSUERO>
        <PUBLICKEY>{PUBLICKEY}</PUBLICKEY>
        <SERIALNUMBER>{SERIALNUMBER}</SERIALNUMBER>
        <VALIDUNTIL>{VALIDUNTIL}</VALIDUNTIL>
        <CPF>{CPF}</CPF>
        <EMAIL>{EMAIL}</EMAIL>
        <IDParceiroWS>{ID}</IDParceiroWS>
      </oRequest>
    </LoginUsuarioCertificado>
  </soap12:Body>
</soap12:Envelope>'''

    headers = {
        'Content-type': 'application/soap+xml; charset=utf-8',
    }
    r = requests.post(
        f'{URL}/login.asmx',
        data=body,
        headers=headers,
    )

    print(f'Status code: {r.status_code}')


    print('Headers:\n')
    for h in r.headers:
        print(f'\t- {h}: {r.headers[h]}')

    print(r.text)
    return r.content

    # print(r.raw)

    # for i in dir(response):
    #     print(i)
    # self.token = response.json().get('access_token')

# if len(tokens) == 0:
#     create_token()






# BASE64 = base64.b64encode(f"{getenv('ONR_CLIENTKEY')}:{getenv('ONR_CLIENTSECRET')}".encode()).decode()
# scope = 'cobv.read cobv.write cob.read cob.write pix.read pix.write webhook.read webhook.write'
# cert = ('/flask/cert.crt', '/flask/cert.key')

# dias_vencimento = 1

# class Bradesco:
#     """Comunica com a API Pix do Bradesco"""
#     def __init__(self):
#         self.get_token()
#         # if not self.token:
#         #     return {'error': 'Não foi possível gerar o token'}

#     def get_token(self):
#         try:
#             response = requests.post(
#                 f'{URL}/oauth/token',
#                 data = {
#                     'grant_type': 'client_credentials',
#                     'scope': scope
#                 },
#                 headers = {
#                     'Authorization': f'Basic {BASE64}',
#                     'Content-type': 'application/x-www-form-urlencoded'
#                 },
#                 cert = cert
#             )
#             self.token = response.json().get('access_token')
#         except Exception as e:
#             print(e)
            

#     def nova_cobranca(self, txid, cpf, nome, valor, msg):
#         vencimento = datetime.now(pytz.timezone('America/Sao_Paulo')).date() + timedelta(days=dias_vencimento)
#         response = requests.put(
#             f'{URL}/v2/cobv-emv/{txid}',
#             json = {
#                 'chave': KEY,
#                 'devedor': {'cpf': cpf, 'nome': nome},
#                 'valor': {'original': valor},
#                 "calendario": {
#                     "dataDeVencimento": vencimento.isoformat(),
#                     "validadeAposVencimento": 0 },
#                 'solicitacaoPagador': msg
#             },
#             headers = {'Authorization': f'Bearer {self.token}'},
#             cert = cert
#         )
#         print(response.status_code)
#         print(json.dumps(response.json(), indent=4))
#         return response.json()

#     def revisa_cobranca(self, txid):
#         response = requests.patch(
#             f'{URL}/v2/cobv/{txid}',
#             json = {
#                 'status': 'REMOVIDA_PELO_USUARIO_RECEBEDOR'
#             },
#             headers = {'Authorization': f'Bearer {self.token}'},
#             cert = cert
#         )
#         print(response.status_code)
#         print(json.dumps(response.json(), indent=4))

#     def ver_cobranca(self, txid):
#         response = requests.get(
#             f'{URL}/v2/cobv/{txid}',
#             headers = {'Authorization': f'Bearer {self.token}'},
#             cert = cert
#         )
#         print(response.status_code)
#         print(json.dumps(response.json(), indent=4))

#     def listar_cobrancas(self, days=2, page=0, per_page=10):

#         # 'inicio': '2022-01-10T18:00:00.000Z',
#         # 'fim': '2022-01-12T10:00:00.000Z',

#         inicio = datetime.now(pytz.timezone('America/Sao_Paulo'))-timedelta(days=days)
#         response = requests.get(
#             f'{URL}/v2/cobv',
#             params = {
#                 'inicio': str(inicio.isoformat())+'Z',
#                 'fim': str(datetime.now().isoformat())+'Z',
#                 'paginacao': {
#                     'paginaAtual': page,
#                     'itensPorPagina': per_page
#                 }
#             },
#             headers = {'Authorization': f'Bearer {self.token}'},
#             cert = cert
#         )
#         print(response.status_code)
#         print(json.dumps(response.json(), indent=4))
