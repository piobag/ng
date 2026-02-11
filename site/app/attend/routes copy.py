import re
import base64
from os import path
from io import BytesIO
from bson.objectid import ObjectId
from datetime import datetime, timezone
import pytz
import jwt
from pytz import timezone as pytz_timezone

from werkzeug.utils import secure_filename
from flask import request, abort, current_app, send_file, render_template, jsonify
from flask_login import login_required, current_user
from flask_babel import _
from mongoengine.errors import ValidationError, NotUniqueError

from . import bp, Attend, Nature, Service, Document
from .. import db
from ..auth import check_roles, get_json, get_roles, notify
from ..auth.cpfcnpj import verify_cpfcnpj
from ..finance import Payment
from ..finance.company import CompanyBind
from ..booking import Booking
from ..base import Event, File, get_datatable, User
from ..base.qrcode import get_qrcode
from .import_xls import import_xls

tz = pytz.timezone('America/Sao_Paulo')


### Import XLSX
@bp.get('/import')
@login_required
def import_carta():
    # Captura a resposta da função import_xls
    response = import_xls()

    # Verifica se a resposta é válida
    if response:
        return response  # Retorna a resposta gerada por import_xls
    else:
        # Retorna uma resposta padrão caso a função não forneça nada
        return jsonify({"message": "No response from import_xls"}), 500


### Calc Emolumentos XLSX
@bp.get('/calc')
@login_required
def calc_value():
    # Dados fornecidos
    atos_old = {
        'correio': 18.05,
        'taxa': 17.68,
        'intimacao': 10.67,
        'cancelamento': 53.30,
        'faixa': {
            '3132': {62.59: 23.97},
            '3133': {125.18: 34.66},
            '3134': {250.35: 63.95},
            '3135': {375.54: 98.60},
            '3136': {500.72: 157.21},
            '3137': {625.89: 178.54},
            '3138': {1251.79: 242.50},
            '3139': {2503.58: 327.78},
            '3140': {6258.95: 434.36},
            '3141': {12517.88: 658.19},
            '3142': {25035.77: 868.70},
            '3143': {float('inf'): 1087.19},
        },
    }

    atos = {
        'correio': 18.05,
        'taxa': 18.43,
        'intimacao': 11.15,
        'cancelamento': 55.67,
        'faixa': {
            '3132': {65.38: 25.02},
            '3133': {130.76: 36.20},
            '3134': {261.52: 66.80},
            '3135': {392.29: 102.99},
            '3136': {523.05: 164.22},
            '3137': {653.80: 186.50},
            '3138': {1307.62: 253.32},
            '3139': {2615.24: 342.41},
            '3140': {6538.10: 453.72},
            '3141': {13076.18: 687.54},
            '3142': {26152.37: 907.44},
            '3143': {float('inf'): 1135.68},
        },
    }


    # Função para calcular o valor final
    def calcular_valor(valor_input, codigo):
        resultado = {}
        valor_base = 0

        if codigo in atos['faixa']:
            faixas = atos['faixa'][codigo]

            # Encontra o menor limite maior ou igual ao valor_input
            limite_mais_proximo = min((limite for limite in faixas if limite >= valor_input), default=None)

            if limite_mais_proximo is not None:
                valor_base = faixas[limite_mais_proximo]
                resultado['valor_base'] = valor_base
            else:
                return None  # Nenhuma faixa válida encontrada

        elif codigo in atos:  # Para valores diretos ('correio', 'taxa', etc.)
            valor_base = atos[codigo]
            resultado['valor_base'] = valor_base
        else:
            return None  # Código inválido

        # # Calcula os incrementos e o valor final
        # if codigo in ['correio', 'taxa']:
        #     resultado['incremento_21'] = 0
        #     resultado['iss_5'] = 0
        #     resultado['valor_final'] = valor_base
        # else:
        #     incremento_21 = round(valor_base * 0.2125, 2)
        #     iss_5 = round(valor_base * 0.05, 2)
        #     resultado['incremento_21'] = incremento_21
        #     resultado['iss_5'] = iss_5
        #     resultado['valor_final'] = round(valor_base + incremento_21 + iss_5, 2)



        # Calcula os incrementos e o valor final
        if codigo in ['correio', 'taxa']:
            resultado['fundesp_10'] = 0
            resultado['funemp_3'] = 0
            resultado['fucomp_6'] = 0
            resultado['fepasaj_2'] = 0
            resultado['funproge_2'] = 0
            resultado['fundepeg_1_25'] = 0
            resultado['iss_5'] = 0
            resultado['valor_final'] = valor_base
        else:
            fundesp_10 = round(valor_base * 0.1, 2)
            funemp_3 = round(valor_base * 0.03, 2)
            fucomp_6 = round(valor_base * 0.06, 2)
            fepasaj_2 = round(valor_base * 0.02, 2)
            funproge_2 = round(valor_base * 0.02, 2)
            fundepeg_1_25 = round(valor_base * 0.0125, 2)
            iss_5 = round(valor_base * 0.05, 2)
            resultado['fundesp_10'] = fundesp_10
            resultado['funemp_3'] = funemp_3
            resultado['fucomp_6'] = fucomp_6
            resultado['fepasaj_2'] = fepasaj_2
            resultado['funproge_2'] = funproge_2
            resultado['fundepeg_1_25'] = fundepeg_1_25
            resultado['iss_5'] = iss_5
            resultado['valor_final'] = round(valor_base + fundesp_10 + funemp_3 + fucomp_6 + fepasaj_2 + funproge_2 + fundepeg_1_25 + iss_5, 2)

        return resultado

    # Valor de entrada
    valor_input = 2710.47

    # Códigos a serem considerados
    codigos_a_considerar = [
        'correio', 'taxa', 'intimacao', 'cancelamento',
        '3132', '3133', '3134', '3135', '3136', '3137', 
        '3138', '3139', '3140', '3141', '3142', '3143'
    ]

    total_valores_finais = 0  # Acumula o total
    faixa_selecionada = False  # Controla se já encontrou a faixa válida

    # Calcula e exibe os resultados
    for codigo in codigos_a_considerar:
        if faixa_selecionada and codigo in atos['faixa']:
            break  # Para de iterar após encontrar e calcular a faixa válida

        resultado = calcular_valor(valor_input, codigo)

        if resultado is not None:
            print(f"Código: {codigo}")
            print(f"Valor Base: {resultado['valor_base']}")
            # print(f"Incremento de 21,25% (Arredondado): {resultado['incremento_21']}")
            print(f"Incremento de 5% (Arredondado): {resultado['iss_5']}")
            print(f"Valor Final: {resultado['valor_final']:.2f}")
            print('-' * 30)

            total_valores_finais += resultado['valor_final']

            # Marca a faixa como selecionada
            if codigo in atos['faixa']:
                faixa_selecionada = True

    # Exibe o total final
    print(f"Total dos Valores Finais: {total_valores_finais:.2f}")
    return f"Total dos Valores Finais: {total_valores_finais:.2f}"


### Attend
@bp.get('/') # Get Attends
@login_required
@check_roles(['ri', 'fin', 'itm'])
def index():
    attend = Attend.objects.filter(func=current_user.id, end=None).first()
    if attend:
        result = attend.to_dict()
        return {'result': result}
    else:
        return {
            'noresult': True,
        }

@bp.get('/info') # Get Attend Info
@login_required
@check_roles(['ri', 'fin'])
def get_info():
    id = request.args.get('id')
    if not (id and len(id) == 24):
        abort(400)
    result = {'result': Attend.objects.get_or_404(id=id).to_info()}
    return result

@bp.get('/prot/info') # Get Prot Info
@login_required
@check_roles(['ri', 'fin', 'itm'])
def prot_info():
    id = request.args.get('id')
    if not (id and len(id) == 24):
        abort(400)
    next = request.args.get('next')
    prev = request.args.get('prev')
    if next:
        prot = Service.objects.filter(id=id).only('prot').first()
        if not prot: abort(400)
        next_prot = Service.objects.filter(prot__gt=prot.prot).first() #.limit(1)
        if not next_prot: abort(404)
        result = {'result': next_prot.to_info()}
    elif prev:
        prot = Service.objects.filter(id=id).only('prot').first()
        if not prot: abort(400)
        prev_prot = Service.objects.filter(prot__lt=prot.prot).order_by('-prot').first()
        if not prev_prot: abort(404)
        result = {'result': prev_prot.to_info()}
    else:
        result = {'result': Service.objects.get_or_404(id=id).to_info()}
    return result

@bp.get('/list') # Get Documents
@login_required
@check_roles(['ri', 'adm'])
@get_datatable
def list(dt):
    attends = Service.objects(s_print__ne=True)
    return jsonify([attend.to_list() for attend in attends])

    # list = attends.order_by('-timestamp').skip(dt['start'])
    # fromdate = tz.localize(datetime.strptime(f'{request.args.get("from", str(datetime.now(tz).date()))} 00', '%Y-%m-%d %H')).astimezone(pytz.utc).timestamp()
    # enddate = tz.localize(datetime.strptime(f'{request.args.get("end", str(datetime.now(tz).date()))} 23:59:59', '%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc).timestamp()
    # if enddate and not fromdate:
    #     return {'error': 'Selecione a data inicial.'}, 400
    
    # attends = Attend.objects(func=current_user.id, end__gt=fromdate, end__lt=enddate)
    # total_filtered = attends.count()
    # list = attends.order_by('-timestamp').skip(dt['start']).limit(dt['length'])


    # return {
    #     'result': [x.to_info() for x in list],
    #     'total': total_filtered,
    # }

@bp.get('/chart') # Get Chart
@login_required
@check_roles(['ri', 'adm'])
@get_datatable
def chart(dt):
    if dt['filter']:
        match dt['filter']:
            case 'Importado':
                # total_filtered = Service.objects(s_print__ne=False).count()
                list = Service.objects(s_print__ne=True).order_by('-timestamp').skip(dt['start']).limit(dt['length'])
                total_filtered = list.count()
                return {
                    'result': [x.to_list() for x in list],
                    'total': total_filtered,
                }
            case 'Impresso':
                attend = Service.objects.filter(s_print=True,  s_take__ne=True,  s_paid__ne=True)
                result = [x.to_list() for x in attend.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = attend.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Entregue':
                attend = Service.objects.filter(s_take=True, s_paid__ne=True)
                result = [x.to_list() for x in attend.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = attend.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Pago':
                attend = Service.objects.filter(s_paid=True, s_take=True)
                result = [x.to_list() for x in attend.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = attend.count()
                return {
                    'result': result,
                    'total': total,
                }
            case _:
                abort(400)

    # total_filtered = Service.objects().count()
    # list = Service.objects().order_by('name').skip(dt['start']).limit(dt['length'])
    return {
        'result': [x.to_info() for x in list],
        'total': total_filtered,
    }


@bp.get('/status') # Get Graph
@login_required
@check_roles(['ri'])
def get_status():
    impor = Service.objects(s_print__ne=True).count()
    printed = Service.objects(s_print=True,  s_take__ne=True,  s_paid__ne=True).count()
    take = Service.objects(s_take=True, s_paid__ne=True).count()
    paid = Service.objects(s_paid=True, s_take=True).count()

    return {'result': [
        ('Importado', impor),
        ('Impresso', printed),
        ('Entregue', take),
        ('Pago', paid),
    ]}



def get_attend_info(id):
    a = Attend.objects.get_or_404(id=id)
    attend = {
        'id': str(a.id),

        'name': a.user.name,
        'cpf': a.user.cpfcnpj,
        'end': a.end,
        'email': a.user.email or None,

        'saldo': 0.0,
        'paid': 0.0,
        'to_pay': 0.0,
        'total': 0.0,
    }
    # Pagamentos confirmados no atendimento
    for p in Payment.objects.filter(attend=a, confirmed__ne=None):
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

# GET
@bp.get('/finance') # Get Finance
@login_required
@check_roles(['ri', 'fin'])
@get_datatable
def finance(dt):
    fromdate = tz.localize(datetime.strptime(f'{request.args.get("from", str(datetime.now(tz).date()))} 00', '%Y-%m-%d %H')).astimezone(pytz.utc).timestamp()
    enddate = tz.localize(datetime.strptime(f'{request.args.get("end", str(datetime.now(tz).date()))} 23:59:59', '%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc).timestamp()
    if enddate and not fromdate:
        return {'error': 'Selecione a data inicial.'}, 400

    total_payments = {}

    for p in Payment.objects.filter(func=current_user.id, attend__ne=None, confirmed__gt=fromdate, confirmed__lt=enddate):
        if total_payments.get(p.type):
            total_payments[p.type] += p.value
        else:
            total_payments[p.type] = p.value
    
    return {'result': 1, 'total_payments': total_payments}

@bp.get('/search') # Search Prot
@login_required
@check_roles(['ri', 'fin', 'itm', 'ng'])
@get_roles
def search(roles):
    text = request.args.get('text')
    text = str(text)
    if not text:
        return {'result': []}
    prots = Service.objects.filter(prot_cod=text)
    return {'result': [x.to_event() for x in prots]}



# POST
@bp.post('/') # New Attend
@login_required
@check_roles(['ri'])
@get_json
def new(data):
    start = datetime.utcnow().timestamp()
    cpf = re.sub('\D', '', data['cpf'])
    if not verify_cpfcnpj(cpf):
        return {'error': _('Invalid CPF')}, 400

    name = data['name'].strip().title()

    if Attend.objects.filter(func=current_user.id, end=None).first():
        return {'error': _('There is a service in progress')}

    # Salvar dados atualizados
    user = User.objects.filter(cpfcnpj=cpf).first()
    if user:
        save = False
        if user.name != name:
            user.name = name
            save = True
        if save:
            user.save()
    else:
        # user = User.objects.filter(email=email).first()
        # if user:
        #     if user.cpfcnpj:
        #         return {'error': 'Email cadastrado em outra conta com o CPF {user.cpfcnpj}'}, 400
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
        )
        user.save()
    try:
        attend = Attend(
            user=user,
            func=current_user.id,
            start=start,
            timestamp=start,
        )
        attend.save()
        return {'result': str(attend.id)}
    except Exception as e:
        msg = _('Error saving to database')
        notify(msg, e)
        return {'error': msg}, 400

@bp.post('/import') # Import Service
@login_required
@check_roles(['ri'])
@get_json
def import_service(data):
    id = data.get('id')
    if not (id and len(id) == 24):
        abort(400)
    files = data.get('files')
    if not files:
        return {'error': 'Nenhum arquivo encontrado'}, 400
    result = {}
    for f in files:
        filename = secure_filename(f['fileName'])
        if not path.splitext(filename)[1].lower() in ['.p7s', '.pdf']:
            return {'error': 'Tipo de arquivo inválido'}, 400
        if not f.get('data'):
            return {'error': 'Tipo de arquivo inválido'}, 400
        content = base64.b64decode(f['data'])
        # Test content type
        from app.base.ocr import extract_text_from_pdf
        text = extract_text_from_pdf(content)
        # print(text)

        # Ordem
        ordem_re = re.compile(r"mero de ordem: (\d+)").search(text)
        if not ordem_re:
            return {'error': 'Não foi possível identificar o número de Ordem'}, 400
        result['ordem'] = ordem_re.group(1)

        # Atendimento
        attend_re = re.compile(r"igo do atendimento: (\S+)").search(text)
        if not attend_re:
            return {'error': 'Não foi possível identificar o código de Atendimento'}, 400
        result['attend'] = attend_re.group(1)

        # # Matricula
        # matricula_re = re.compile(r"Registro Geral: .* \((\d+)\)").search(text)
        # if not matricula_re:
        #     return {'error': 'Não foi possível identificar o número de Matricula'}, 400
        # print(f'Matrícula: {matricula_re.group(1)}')

        # Total Pago
        pago_re = re.compile(r"R\$(\d+\.?\d+,\d{2})\n\nTotal").search(text)
        if not pago_re:
            return {'error': 'Não foi possível identificar valor Pago'}, 400
        result['pago'] = pago_re.group(1).replace('.', '').replace(',', '.')

        # Total Restante
        restante_re = re.compile(r"R\$(\d+\.?\d+,\d{2})\n\nObs:").search(text)
        if not restante_re:
            return {'error': 'Não foi possível identificar valor Restante'}, 400
        result['restante'] = restante_re.group(1).replace('.', '').replace(',', '.')

        return result


    # Dando certo a extração de dados
    # Identificar o attend e incluir os serviços


    # status = 'Event'
    # event = Event(
    #     timestamp = datetime.utcnow().timestamp(),
    #     actor = current_user.id,
    #     action = 'create',
    #     object = 'payment',
    #     target = new_p.to_event(),
    # )
    # event.save()
    # e_created.append(str(event.id))

    return {'result': 'dados'}

@bp.post('/service') # Save Service
@login_required
@get_json
@check_roles(['ri'])
def post_service(data):
    id = data.get('attend')
    if not (id and len(id) == 24):
        abort(400)
    attend = Attend.objects.get_or_404(id=id)

    try:
        new_s = Service(
            prot_cod=int(data.get('prot_cod')),
            attend=attend.id,
            end_bai=data.get('end_bai'),
            end_cep=int(data.get('end_cep')),
            end_cid=data.get('end_cid'),
            end_log=data.get('end_log'),
            end_uf=data.get('end_uf'),
            prot_emi=int(data.get('prot_emi')),
            prot_esp=data.get('prot_esp'),
            prot_fls=data.get('prot_fls'),
            prot_liv=data.get('prot_liv'),
            prot_num=int(data.get('prot_num')),
            prot_tot_c=data.get('prot_tot_c'),
            prot_tot_p=data.get('prot_tot_p'),
            prot_val=data.get('prot_val'),
            prot_ven=int(data.get('prot_ven')) if data.get('prot_ven') else None,
            prot_date=int(data.get('prot_date')),
            s_start=True,
            timestamp=datetime.now(timezone.utc).timestamp(),
        )

        new_s.save()

        attend.end = datetime.now(timezone.utc).timestamp()
        attend.save()

        # Evento
        event = Event(
            timestamp=datetime.utcnow().timestamp(),
            actor=current_user.id,
            action='create',
            object='service',
            target=new_s.to_list(),
        )
        event.save()

        return jsonify({'result': str(new_s.id)}), 201

    except NotUniqueError:
        # Mensagem amigável para erro de duplicação
        return jsonify({
            'status': 'error',
            'message': f"Numero de protocolo '{data.get('prot_cod')}' já cadastrado no sistema."
        }), 409  # HTTP 409 Conflict

    except ValidationError as ve:
        # Mensagem amigável para erros de validação
        return jsonify({
            'status': 'error',
            'message': f"Validation error: {str(ve)}"
        }), 400  # HTTP 400 Bad Request

    except Exception as e:
        # Erros inesperados
        return jsonify({
            'status': 'error',
            'message': f"An unexpected error occurred: {str(e)}"
        }), 500  # HTTP 500 Internal Server Error

@bp.post('/payment') # New Payment
@login_required
@check_roles(['ri'])
@get_json
def post_payment(data):
    id = data.get('id')
    ptype = data.get('type')
    pvalue = data.get('value')
    id = data.get('id')
    if not (id and len(id) == 24 and ptype and pvalue):
        abort(400)
    
    attend = Attend.objects.get_or_404(id=id)

    f_created = []
    p_created = []
    e_created = []
    # try:
    pending = current_app.config['PAYMENTS'][ptype].get('pending')

    status = 'File'
    files = data.get('files')
    if files:
        filename = secure_filename(files[0]['fileName'])
        content = base64.b64decode(files[0]['data'])
        bcontent = BytesIO(content)
        newfile = File(
            user = current_user.id,
            timestamp = datetime.utcnow().timestamp(),
            name = filename,
            content_type = files[0]['fileType'],
            attend = attend.id,
        )
        newfile.file.put(bcontent, app='attend', attend=str(attend.id), filename=filename, content_type=files[0]['fileType'])
        newfile.save()
        f_created.append(newfile.id)

    status = 'Payment'
    new_p = Payment(
        attend=attend.id,
        user=attend.user.id,
        func=current_user.id,
        type=ptype,
        value=float(pvalue),
        confirmed = None if pending else datetime.utcnow().timestamp(),
        compr = newfile.id if files else None,
        timestamp = datetime.utcnow().timestamp(),
    )
    new_p.save()
    p_created.append(str(new_p.id))

    status = 'Event'
    event = Event(
        timestamp = datetime.utcnow().timestamp(),
        actor = current_user.id,
        action = 'create',
        object = 'payment',
        target = new_p.to_event(),
    )
    event.save()
    e_created.append(str(event.id))

    return {'result': 'ok'}

@bp.post('/exig') # Nova Exigência
@login_required
@check_roles(['ri'])
@get_json
def post_exig(data):
    id = data.get('id')
    file = data.get('file')
    if not (id and len(id) == 24 and file):
        abort(400)
    f_created = []

    obj = Service.objects.get_or_404(id=id)
    if obj.exig:
        if not obj.exig_resp:
            return {'error': 'Serviço aguardando resposta de outra exigência'}, 400

    attend = Attend.objects.get_or_404(id=obj.attend.id)

    # File
    filename = secure_filename(file['fileName'])
    content = base64.b64decode(file['data'])
    bcontent = BytesIO(content)
    newfile = File(
        user = current_user.id,
        timestamp = datetime.utcnow().timestamp(),
        name = filename,
        content_type = file['fileType'],
        service = obj.id,
    )
    newfile.file.put(bcontent, app='attend', service=str(obj.id), filename=filename, content_type=file['fileType'])
    newfile.save()
    f_created.append(newfile.id)

    obj.exig_resp = None
    obj.exig = newfile.id
    obj.save()

    # Event
    event = Event(
        timestamp = datetime.now(timezone.utc).timestamp(),
        actor = current_user.id,
        action = 'create',
        object = 'exig',
        target = obj.to_event(),
    )
    event.save()



    match obj.send_exigencia():
        case '0':
            return {'result': 1}
        case '403':
            return {'error': 'Valide o qrcode enviado para o email'}, 400
        case '402':
            return {'error': 'Número Inválido'}, 400
            # Email User Attend
            # exig = {
            #     'name': attend.user.name,
            #     'prot': obj.prot,
            #     'date': obj.timestamp,
            # }
            # obj.send_mail(exig=exig)
        case '401':
            return {'error': 'Erro'}, 400
        case _:
            abort(400)

    return {'result': 'ok'}

@bp.post('/comment') # New Comment Attend
@login_required
@check_roles(['ri'])
@get_json
def comment(data):
    id = data.get('id')
    comment = data.get('comment')
    if not (id and len(id) == 24 and comment):
        abort(400)
    attend = Attend.objects.get_or_404(id=id)
    target = attend.to_event()
    target['comment'] = comment.strip()
    event = Event(
        timestamp = datetime.utcnow().timestamp(),
        actor = current_user.id,
        action = 'comment',
        object = 'attend',
        target = target,
    )
    event.save()
    return {'result': str(attend.id)}

@bp.post('/service/comment') # New Comment Service
@login_required
@check_roles(['ri'])
@get_json
def prot_comment(data):
    id = data.get('id')
    comment = data.get('comment')
    if not (id and len(id) == 24 and comment):
        abort(400)
    service = Service.objects.get_or_404(id=id)

    target = service.to_event()
    target['comment'] = comment.strip()

    event = Event(
        timestamp = datetime.utcnow().timestamp(),
        actor = current_user.id,
        action = 'comment',
        object = 'service',
        target = target,
    )
    event.save()
    return {'result': str(event.id)}

@bp.post('/service/docs') # Envio de Documentos faltantes do Serviço
@get_json
def post_service_docs(data):
    id = data.get('id')
    if not (id and len(id) == 24):
        abort(400)
    docs = data.get('docs')
    if not (docs and len(docs) > 0):
        return {'error': 'Envie os docs'}, 400
    service = Service.objects.get_or_404(id=id)

    for d in docs:
        if len(docs[d]) == 0:
            continue
        doc = Doc.objects.get_or_404(id=d, service=service.id)
        if doc.entregue:
            return {'error': f'Documento "{doc.name}" já foi entregue.'}, 400
        fcreated = []
        for f in docs[d]:
            fname = secure_filename(f.get('name'))
            ftype = f.get('type')
            fdata = f.get('data')
            if not (fname and ftype and fdata):
                return {'error': f'Arquivo incompleto.'}, 400
            content = base64.b64decode(fdata)
            bcontent = BytesIO(content)
            file = File(
                timestamp = datetime.now(timezone.utc).timestamp(),
                name= fname,
                content_type= ftype.strip(),
                attend = service.attend.id,
                service= service.id,
                user= service.attend.user.id,
            )
            file.file.put(bcontent, app='attend', attend=str(service.attend.id), filename=fname, content_type=ftype)
            file.save()
            fcreated.append(file.id)
        doc.files = fcreated
        doc.entregue = True
        doc.save()
    return {'result': '1'}


# PUT
@bp.put('/') # Edit / End Attend
@login_required
@get_json
@check_roles(['ri'])
def edit(data):
    id = data.get('id')
    if not (id and len(id) == 24 and data.get('action')):
        abort(400)
    s_created = []
    p_created = []
    f_created = []
    e_created = []
    docs_created = []
    try:
        if data['action'] == 'pay':
            status = 'Service'
            svc = Service.objects.get_or_404(id=data['id'], attend__ne=None)
            if svc.total == svc.paid:
                return {'error': f"Serviço já pago"}, 400
            # Buscar serviços e pagamentos vinculados
            if svc.attend.user.pj:
                services = 0.0
                for a in Attend.objects.filter(user=svc.attend.user):
                    services += sum([x.paid for x in Service.objects.filter(attend=a.id).only('paid')])
                payments = sum([x.value for x in Payment.objects.filter(user=svc.attend.user, confirmed__ne=None, attend__ne=None).only('value')])
                deposits = sum([x.value for x in Payment.objects.filter(user=svc.attend.user, confirmed__ne=None, attend=None).only('value')])
                saldo = round(payments + deposits - services, 2)
            else:
                services = sum([x.paid for x in Service.objects.filter(attend=svc.attend).only('paid')])
                payments = sum([x.value for x in Payment.objects.filter(attend=svc.attend, confirmed__ne=None).only('value')])
                saldo = round(payments - services, 2)

            paying = round(svc.total - svc.paid, 2)
            if saldo < paying:

                return {'error': f"Atendimento sem saldo"}, 400

            status = 'Event'
            t_event = svc.to_event()
            t_event['paying'] = paying
            event = Event(
                timestamp = datetime.utcnow().timestamp(),
                actor = current_user.id,
                action = data['action'],
                object = 'service',
                target = t_event,
            )
            svc.paid = float(svc.total)

            status = 'Save Event'
            event.save()
            e_created.append(str(event.id))

            status = 'Paying' 
            svc.save()

            return {'result': 'Ok'}
        if data['action'] == 'end':
            status = 'End'
            attend = Attend.objects.get_or_404(id=id)

            status = 'Payments'
            for p in data['payments']:
                pending = current_app.config['PAYMENTS'][p['type']].get('pending')
                new_p = Payment(
                    attend=attend.id,
                    user=attend.user.id,
                    func=current_user.id,
                    type=p['type'],
                    value=float(p['value']),
                    confirmed = None if pending else datetime.utcnow().timestamp(),
                    timestamp = datetime.utcnow().timestamp(),
                )
                new_p.save()
                p_created.append(str(new_p.id))

            # Gravar arquivos no banco
            status = 'Files'
            files = data.get('files')
            for f in files or []:
                filename = secure_filename(f['fileName'])
                content = base64.b64decode(f['data'])
                bcontent = BytesIO(content)
                newfile = File(
                    user = current_user.id,
                    timestamp = datetime.utcnow().timestamp(),
                    name = filename,
                    content_type = f['fileType'],
                    attend = attend.id,
                )
                newfile.file.put(bcontent, app='attend', attend=str(attend.id), filename=filename, content_type=f['fileType'])
                newfile.save()
                f_created.append(newfile.id)

            status = 'Comment'
            comment = data.get('comment')
            if comment and comment.strip():
                comment = Event(
                    timestamp = datetime.utcnow().timestamp(),
                    actor = current_user.id,
                    action = 'comment',
                    object = 'attend',
                    target = {
                        'id': str(attend.id),
                        'comment': comment.strip(),
                    },
                )
                comment.save()
                e_created.append(str(comment.id))

            status = 'Event'
            event = Event(
                timestamp = datetime.utcnow().timestamp(),
                actor = current_user.id,
                action = data['action'],
                object = 'attend',
                target = attend.to_list(),
            )
            event.save()
            e_created.append(str(event.id))

            status = 'Attend'
            attend.end = datetime.utcnow().timestamp()
            attend.save()
            return {'result': 'Ok'}
    except Exception as e:
        msg = f"{_('Error saving to database')} | {status}"
        notify(msg, e)
        for i in docs_created:
            to_del = Doc.objects.filter(id=i).first()
            if to_del:
                to_del.delete()
        for i in s_created:
            to_del = Service.objects.filter(id=i).first()
            if to_del:
                to_del.delete()
        for i in p_created:
            to_del = Payment.objects.filter(id=i).first()
            if to_del:
                to_del.delete()
        for i in f_created:
            to_del = File.objects.filter(id=i).first()
            if to_del:
                f.file.delete()
                f.delete()
        for i in e_created:
            to_del = Event.objects.filter(id=i).first()
            if to_del:
                to_del.delete()
        return {'error': msg}, 400
    abort(404)

@bp.put('/prot') # Edit Prot
@login_required
@get_json
@get_roles
@check_roles(['ri', 'adm'])
def put_prot(roles, data):
    id = data.get('id')
    if not (id and len(id) == 24 and data.get('action')):
        abort(400)
    if data['action'] == 'edit':

        svc = Service.objects.get_or_404(id=data['id'])
        if not svc.attend:
            return {'error': 'Serviço não é do Atendimento'}, 400
        to_event = svc.to_event()
        e_created = []

        # Cria um dicionário com os valores convertidos e validados
        service_data = {
            "prot_cod": int(data.get('prot_cod')),
            "end_bai": data.get('end_bai'),
            "end_cep": int(data.get('end_cep')),
            "end_cid": data.get('end_cid'),
            "end_log": data.get('end_log'),
            "end_uf": data.get('end_uf'),
            "prot_emi": int(data.get('prot_emi')),
            "prot_esp": data.get('prot_esp'),
            "prot_num": int(data.get('prot_num')),
            "prot_fls": data.get('prot_fls'),
            "prot_liv": data.get('prot_liv'),
            "prot_val": data.get('prot_val'),
            "prot_tot_c": data.get('prot_tot_c'),
            "prot_tot_p": data.get('prot_tot_p'),
            "prot_ven": int(data.get('prot_ven')) if data.get('prot_ven') else None,
            "prot_date": int(data.get('prot_date')),
            "prot_apr": data.get('prot_apr'),
            "prot_ced": data.get('prot_ced'),
            "prot_sac": data.get('prot_sac'),
            "prot_sac_doc": data.get('prot_sac_doc'),
        }
        # Remove chaves com valores None
        filtered_data = {key: value for key, value in service_data.items() if value is not None}

        try:
            # Atualiza os campos do objeto
            for key, value in filtered_data.items():
                setattr(svc, key, value)
            svc.save()
            event = Event(
                timestamp = datetime.utcnow().timestamp(),
                actor = current_user.id,
                action = data['action'],
                object = 'service',
                target = to_event,
            )
            event.save()
            e_created.append(str(event.id))
            return {'result': 'Ok'}
        except NotUniqueError as e:
           # Tratamento para duplicação de chave única
            return {
                'status': 'error',
                'message': 'Duplicate prot_cod detected',
                'details': str(e),
            }
        except ValidationError as e:
            # Tratamento para validações de esquema
            return {
                'status': 'error',
                'message': 'Validation error',
                'details': str(e),
            }
        except Exception as e:
            # Tratamento genérico de erros
            return {
                'status': 'error',
                'message': 'An unexpected error occurred',
                'details': str(e),
            }
    if data['action'] == 'print':
        svc = Service.objects.get_or_404(id=data['id'])
        try:
            svc.s_print = True
            svc.save()
            return {'result': 'ok'}

        except Exception as e:
            notify('Erro alterando serviço', e)
            abort(400)

    if data['action'] == 'paid':
        svc = Service.objects.get_or_404(id=data['id'])
        try:
            svc.s_paid = True
            svc.save()
            return {'result': 'ok'}

        except Exception as e:
            notify('Erro alterando serviço', e)
            abort(400)

    if data['action'] == 'take':
        svc = Service.objects.get_or_404(id=data['id'])
        try:
            svc.s_take = True
            svc.save()
            return {'result': 'ok'}

        except Exception as e:
            notify('Erro alterando serviço', e)
            abort(400)


    # except Exception as e:
    #     msg = f"{_('Error saving to database')} | {status}"
    #     notify(msg, e)
    #     if s_edited:
    #         svc.total = to_event['total']
    #         svc.save()
    #     for i in e_created:
    #         to_del = Event.objects.filter(id=i).first()
    #         if to_del:
    #             to_del.delete()
    #     return {'error': msg}, 400

@bp.put('/docs') # Edit Docs do Prot
@login_required
@get_json
@check_roles(['ri', 'digitizer'])
# def put_docs(data):
def put_docs(data):
    id = data.get('id')
    if not (id and len(id) == 24 and data.get('docs')):
        abort(400)
    svc = Service.objects.get_or_404(id=data['id'])
    to_event = svc.to_event()

    e_created = []
    doc_list = {}   # Lista de Docs não entregues do Service
    for d in Doc.objects.filter(service=svc.id).only('id', 'name', 'entregue'):
        if not d.entregue:
            doc_list[d.name] = d.id
    for d in data['docs']:
        qtd = d.get('qtd')
        if not qtd:
            qtd = 1
        for q in range(0, qtd):
            new_doc = Doc(
                name = d['name'],
                entregue = d['entregue'],
                func_id = current_user.id,
                service = str(svc.id),
                pending = True,
                timestamp = datetime.utcnow().timestamp(),
            ).save()


            # Apagar doc igual não entregue
            if d['name'] in doc_list.keys():
                Doc.objects.get(id=doc_list[d['name']]).delete()

    event = Event(
        timestamp = datetime.utcnow().timestamp(),
        actor = current_user.id,
        action = 'create',
        object = 'docs',
        target = to_event,
    )
    event.save()
    e_created.append(str(event.id))
    return {'result': 'ok'}
    # except Exception as e:
    #     msg = f"{_('Error saving to database')} | {status}"
    #     notify(msg, e)
    #     if s_edited:
    #         svc.total = to_event['total']
    #         svc.save()
    #     for i in e_created:
    #         to_del = Event.objects.filter(id=i).first()
    #         if to_del:
    #             to_del.delete()
    #     return {'error': msg}, 400
    abort(404)

@bp.put('/exig/<token>') # Enviar Resposta Exigência
@get_json
def put_exig(data, token):
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
    id = data_token.get('exig')
    file = data.get('file')
    if not (id and len(id) == 24 and file):
        abort(400)
    svc = Service.objects.get_or_404(id=id)
    if not svc.exig:
        return {'error': 'Serviço sem exigência'}, 400
    if svc.exig_resp:
        return {'error': 'Exigência já respondida'}, 400

    attend = Attend.objects.get_or_404(id=svc.attend.id)

    f_created = []

    # File
    filename = secure_filename(file['fileName'])
    content = base64.b64decode(file['data'])
    bcontent = BytesIO(content)
    newfile = File(
        user = attend.user,
        timestamp = datetime.utcnow().timestamp(),
        name = filename,
        content_type = file['fileType'],
        service = svc.id,
    )
    newfile.file.put(bcontent, app='attend', service=str(svc.id), filename=filename, content_type=file['fileType'])
    newfile.save()
    f_created.append(newfile.id)

    svc.exig_resp = newfile.id
    svc.save()

    return {'result': 'ok'}

# DELETE
@bp.delete('/') # Delete Attend Info
@login_required
@check_roles(['ri'])
@get_json
def delete(data):
    # id = data.get('id')
    # if not (id and len(id) == 24 and data.get('action')):
    #     abort(400)

    attend = Attend.objects.get_or_404(id=data['id'])
    if not attend.func.id == current_user.id:
        abort(401)
    if attend.end:
        return {'error': 'Atendimento já finalizado'}, 400
    try:
        attend.delete_all()
        return {'result': 'deleted'}
    except Exception as e:
        msg = _('Error saving to database')
        notify(msg, e)
        return {'error': msg}, 400

@bp.delete('/service') # Delete Service Current Attend
@login_required
@check_roles(['ri'])
@get_json
def del_prot(data):
    id = str(data.get('id'))
    svc = str(data.get('service'))
    if not (id and len(id) == 24 and svc and len(svc) == 24):
        abort(400)
    attend = Attend.objects.get_or_404(id=id)
    if not attend.func.id == current_user.id:
        abort(401)
    if attend.end:
        return {'error': 'Atendimento já finalizado'}, 400
    service = Service.objects.get_or_404(id=svc)
    try:
        service.delete_all()
        return {'result': 1}
    except Exception as e:
        msg = _('Erro deletando service attend.del_prot')
        notify(msg, e)
        return {'error': msg}, 400

### NATURES
@bp.get('/natures') # Get Natures
@login_required
@check_roles(['ri', 'fin', 'itm', 'settings', 'ng'])
@get_datatable
def natures(dt):
    if dt['search']:
        total_filtered = Nature.objects(enabled=True).search_text(dt['search']).count()
        list = Nature.objects(enabled=True).search_text(dt['search']).skip(dt['start']).limit(dt['length'])
        return {
            'result': [x.to_info() for x in list],
            'total': total_filtered,
        }
    total_filtered = Nature.objects(enabled=True).count()
    list = Nature.objects(enabled=True).order_by('name').skip(dt['start']).limit(dt['length'])
    return {
        'result': [x.to_info() for x in list],
        'total': total_filtered,
    }

@bp.get('/nature/info') # Get Nature Info
@login_required
@check_roles(['settings', 'ri'])
def nature_info():
    id = request.args.get('id')
    if not (id and len(id) == 24):
        abort(400)
    result = Nature.objects.get_or_404(id=id)
    return {'result': result.to_info()}

@bp.post('/nature') # New Nature
@login_required
@check_roles(['settings'])
@get_json
def new_nature(data):
    try:
        Nature(name=data['name'], type=data['type'], group=data['group']).save()
    except db.NotUniqueError as e:
        return {'error': 'Natureza já existente'}
    return {'result': _('Nature created') }

@bp.put('/nature') # Edit Nature
@login_required
@check_roles(['settings'])
@get_json
def put_nature(data):
    id = data.get('id')
    if not (id and len(id) == 24):
        abort(400)
    docs = data.get('docs')
    for doc in docs:
        if not len(doc) == 24:
            abort(400)
    nature = Nature.objects.get_or_404(id=id)
    nature.docs = [ObjectId(x) for x in docs]
    nature.save()

    # e_created = []
    # try:
    #     event = Event(
    #         timestamp = datetime.utcnow().timestamp(),
    #         actor = current_user.id,
    #         action = data['action'],
    #         object = 'attend',
    #         target = attend.to_dict(),
    #     )
    #     event.save()
    #     e_created.append(str(event.id))

    #     status = 'Attend'
    #     attend.save()

    # except Exception as e:
    #     msg = f"{_('Error saving to database')} | {status}"
    #     notify(msg, e)
    #     for i in s_created:
    #         to_del = Service.objects.filter(id=i).first()
    #         if to_del:
    #             to_del.delete()
    #     for i in p_created:
    #         to_del = Payment.objects.filter(id=i).first()
    #         if to_del:
    #             to_del.delete()
    #     for i in e_created:
    #         to_del = Event.objects.filter(id=i).first()
    #         if to_del:
    #             to_del.delete()
    #     return {'error': msg}, 400

    return {'result': 'Ok'}

@bp.delete('/nature') # Delete Nature
@login_required
@check_roles(['settings'])
@get_json
def del_nature(data):
    id = data.get('id')
    if not (id and len(id) == 24):
        abort(400)
    n = Nature.objects.get_or_404(id=data['id'])
    if not n.enabled:
        return {'error': 'Natureza já desativada'}, 400
    n.enabled = False
    n.save()
    return {'result': 'Ok'}

### Documents
@bp.post('/document') # New Document
@login_required
@check_roles(['settings'])
@get_json
def new_document(data):
    try:
        Document(name=data['name']).save()
    except db.NotUniqueError as e:
        return {'error': 'Documento já existente'}
    return {'result': _('Document created') }

@bp.get('/documents') # Get Documents
@login_required
@check_roles(['ri', 'fin', 'itm', 'settings'])
@get_datatable
def get_documents(dt):
    if dt['search']:
        total_filtered = Document.objects.search_text(dt['search']).count()
        list = Document.objects.search_text(dt['search']).skip(dt['start']).limit(dt['length'])
        return {
            'result': [x.to_list() for x in list],
            'total': total_filtered,
        }
    total_filtered = Document.objects().count()
    list = Document.objects(active=True).order_by('name').skip(dt['start']).limit(dt['length'])
    return {
        'result': [x.to_list() for x in list],
        'total': total_filtered,
    }

@bp.get('/document/info') # Get Document Info
@login_required
@check_roles(['settings'])
def document_info():
    id = request.args.get('id')
    if not (id and len(id) == 24):
        abort(400)
    result = Document.objects.get_or_404(id=id)
    return {'result': result.to_info()}

### COMPANY
# Mover de User para a Company o usuário do Atendimento
@bp.put('/company')
@login_required
@check_roles(['ri'])
@get_json
def put_company(data):
    id = data.get('id')
    company_id = data.get('company')
    if not (id and len(id) == 24 and company_id and len(company_id) == 24):
        abort(400)
    attend = Attend.objects.get_or_404(id=id)
    company = User.objects.get_or_404(id=company_id, pj=True)

    if not CompanyBind.objects.filter(user=attend.user, company=company).first():
        return {'error': f'Usuário não credenciado'}, 400
    attend_event = attend.to_event()
    attend_event['company'] = str(company.id)
    event = Event(
        timestamp = datetime.utcnow().timestamp(),
        actor = current_user.id,
        action = 'company',
        object = 'attend',
        target = attend_event,
    )
    attend.cred = attend.user
    attend.user = company.id

    attend.save()
    event.save()
    return {'result': 'Ok'}

