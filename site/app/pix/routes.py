from . import bp, Pix
from flask import (
    render_template,
    jsonify,
    make_response,
    request,
    abort,
    current_app
)
from flask_login import current_user, login_required
from .bradesco import Bradesco
bradesco = Bradesco()

@bp.route('/tey', methods=['GET', 'POST'])
@login_required
def tey():
    txid = 'NGPix0000955avv3723f809ca5a85'
    cpf = '35984863596'
    nome = 'Maria Alves'
    valor = '359.84'
    msg = 'Atendimento do dia xxx hora xxx'

    response = bradesco.nova_cobranca(txid, cpf, nome, valor, msg)
    print(response)

    # if response['status'] == 400 and response['detail'] == 'The given JWT is invalid':
    #     print('Recriando token')
    #     bradesco.get_token()
    #     response = bradesco.nova_cobranca(txid, cpf, nome, valor, msg)
    return response


@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'GET':
        result = {
            'list': render_template('pix/pix_list.html'),
            'new': render_template('pix/pix_new.html')
        }
        return make_response(jsonify(result), 200)
    abort(404)

# revisa_cobranca('APIPixBradesco0000000000000000000')
# ver_cobranca('APIPixBradesco000000000000000000008')
# listar_cobrancas()
