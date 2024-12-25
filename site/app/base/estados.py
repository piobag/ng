import requests

from flask import request, abort
from flask_login import login_required

from .. import db
from ..base import bp
from ..auth import check_roles

ibge_url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/"


class UF(db.Document):
    sigla = db.StringField(required=True, unique=True)
    municipios = db.ListField()


def update_ufs():
    result = {}
    response = requests.get(ibge_url)
    if response.status_code == 200:
        for i in [x['sigla'] for x in response.json()]:
            print(i)
            uf = requests.get(f'{ibge_url}{i}/municipios')
            if uf.status_code == 200:
                list = []
                for c in [x['nome'] for x in uf.json()]:
                    list.append(c)
                result[i] = list
            else:
                print(f'Erro ao baixar municipios do estado {i}')
                return False
    else:
        print('Erro ao baixar estados')
        return False

    for i in result:
        uf = UF.objects.filter(sigla=i).first()
        if not uf:
            uf = UF(sigla=i)
            uf.save()
        uf.municipios = result[i]
        uf.save()

    print('ok')
    return True

@bp.get('/ufs')
@login_required
@check_roles(['itm', 'fin'])
def get_ufs():
    return {'result': [x.sigla for x in UF.objects().only('sigla')]}


@bp.get('/uf')
@login_required
@check_roles(['itm', 'fin'])
def get_uf():
    sigla = request.args.get('uf')
    if not sigla:
        abort(400)
    uf = UF.objects.get_or_404(sigla=sigla.upper())
    return {'result': uf.municipios}

