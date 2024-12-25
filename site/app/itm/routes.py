from io import BytesIO
from os import path
import re
from datetime import datetime, timezone
import pytz
import base64

import gridfs
import fitz
import pdfkit
from werkzeug.utils import secure_filename
from flask import abort, request, send_file, current_app, render_template, url_for
from flask_login import login_required, current_user
from flask_babel import _
from mongoengine.connection import get_db
from pyhanko import stamp
from asn1crypto import cms
from pyhanko.pdf_utils import text, images
from pyhanko.pdf_utils.font import opentype
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec, append_signature_field

from . import bp, Intimacao, Credor, Visita
from .. import db
from ..auth import check_roles, get_json, notify, get_roles
from ..base import Event, File, get_datatable
from ..base.qrcode import get_qrcode
from ..attend import Service, Nature
from ..finance import Payment, Endereco, Devedor

tz = pytz.timezone('America/Sao_Paulo')
fs = gridfs.GridFS(get_db())

prot_values = {
    'prenot': 10 + 2.62,
    'busca': 16.67 + 4.38,
    'tx': 18.87,
    'cert': 123.49,
    'itm': 150.70 + 39.56,
    'edital': 419.03,
}

# ### Create Naturezas
# nature_itm = Nature.objects.filter(name='Intimação').first()
# if not nature_itm:
#     print('Criando Nature Intimação')
#     nature_itm = Nature(name='Intimação', group='attend', type='prot')
#     nature_itm.save()
# nature_dili = Nature.objects.filter(name='Diligência').first()
# if not nature_dili:
#     print('Criando Nature Diligência')
#     nature_dili = Nature(name='Diligência', group='attend', type='cert')
#     nature_dili.save()
# nature_decur = Nature.objects.filter(name='Decurso').first()
# if not nature_decur:
#     print('Criando Nature Decurso')
#     nature_decur = Nature(name='Decurso', group='attend', type='cert')
#     nature_decur.save()

# nature_itm = nature_itm.id
# nature_dili = nature_dili.id
# nature_decur = nature_decur.id

def get_itm_values(itm):
    total_prenot = round((prot_values['prenot'] + prot_values['busca'] + prot_values['tx']), 2)
    total_prot = total_prenot + (len(itm.pessoas) * prot_values['itm'])
    total = round((total_prot + prot_values['cert'] + (prot_values['cert'] * len(itm.pessoas))), 2)
    return {'total': total, 'total_prot': total_prot, 'total_prenot': total_prenot}

ignore = []
# Extrair dados dos arquivos das Intimações
def read_itm_files():
    for itm in Intimacao.objects():
        svc = False
        try:
            for f in itm.files:
                pass
        except Exception as e:

            # coll = mongo['intimacao']
            # files = mongo['file']
            # itm = coll.find_one({'cod': 'IN00832804C'})
            # print(itm.get('files'))
            # for f in itm['files']:
            #     iid = f['file']
            #     print(iid)
            #     file = files.find_one({'_id': iid})
            #     print(file.get('name'))
            #     print(dir(file))

            # return {'error': f'{itm.cod} sem os arquivos'}, 400
            print(f'{itm.cod} sem os arquivos')
            continue

        if 'files' in dir(itm) and len(itm.files) > 0:
            files = itm.files
        else:
            svc = Service.objects.filter(intimacao=itm.id).first()
            if not svc:
                return 'Sem arquivos e sem serviço vinculado'
            files = svc.files

        credor = False
        pessoas = []
        enderecos = []
        for f in files:
            if not 'content_type' in dir(f):
                print('remove?')
                # files.remove(f)
                # if svc:
                #     svc.save()
                # else:
                #     itm.save()

            # Arquivo p7s
            if f.content_type == 'application/pkcs7-signature':
                content_info: cms.ContentInfo = cms.ContentInfo.load(f.file.read())
                signed_data: cms.SignedData = content_info['content']
                pdf_data = signed_data['encap_content_info']['content'].native
                # with open ('app/teste', 'wb') as f:
                #     f.write(pdf_data)
            elif 'pdf' in f.content_type:
                pdf_data = f.file.read()
            else:
                f.delete()
                files.remove(f)
                if svc:
                    svc.save()
                else:
                    itm.save()
                # return f'Arquivo inválido | {f.name}'
                continue
 
            with fitz.open(stream=pdf_data, filetype='pdf') as doc:
                text = doc[0].get_text()
                if 'CAIXA ECONÔMICA FEDERAL - CNPJ' in text:
                    credor = Credor.objects.filter(name='CAIXA ECONÔMICA FEDERAL').first()
                    if not credor:
                        return {'error': 'Credor não cadastrado no banco de dados, rodar init'}, 400
                    text = text.split('\n')
                    for i in text:
                        if 'Fiduciante(s):' in i:
                            fid = i
                            index = text.index(i)+1
                            # Juntar linhas até "Matricula:"
                            while not 'Matrícula:' in text[index]:
                                fid += ' '+text[index]
                                index += 1

                            p_list = re.findall(r'([A-z]+[ A-z]*) - cpf (\d+)', fid)
                            if not p_list:
                                return {'error': 'Nenhum fiduciante identificado'}, 400
                            for p in p_list:
                                pessoa = {
                                    'name': p[0],
                                    'cpf': p[1][3:] if len(p[1]) ==  14 and p[1].startswith('000') else p[1],
                                }
                                ### Buscar estado civil
                                # # Duas pessoas casadas
                                # x = re.search(r'.*: ([A-z]+[ A-z]*) - cpf (\d+), (\w+) .* comunhão [ a-z]+, ([A-z]+[ A-z]*) - cpf (\d+) *$', pstring)
                                # estcivil = re.search(rf'{p[1]}, (\w+)', fid) or re.search(r'.* - cpf (\d+) *$', fid)
                                # if estcivil:
                                #     pessoa['estcivil'] = estcivil.group(1)
                                pessoas.append(pessoa)

                            # Matrícula
                            x = re.search(r'^Matrícula: ([\d\.]+) *$', text[index])
                            if not x:
                                return {'error': 'Matrícula não encontrada'}, 400
                            matricula = re.sub('\D', '', x.group(1))
                            index += 1

                            # Endereços
                            while not 'demais endereços que estiverem registrados' in text[index]:
                                index += 1
                            if not 'demais endereços que estiverem registrados' in text[index]:
                                return {'error': 'Endereço não encontrado'}, 400

                            print('Demais endereços...')
                            print(text[index])

                            index += 1

                            print('Depois:')
                            print(text[index])

                            def get_endereco(estring):
                                x = re.search(r'^(.*) ([A-Z]{2}) (\d+) *$', estring)
                                if not x:
                                    print(f'Inválido: {estring}')
                                    return {'error': 'Endereço inválido'}, 400
                                endereco = {
                                    'cep': x.group(3),
                                    'estado': x.group(2),
                                }
                                end_split = x.group(1).split(' ')
                                if end_split[-2] == 'CIDADE' and 'OCIDENT' in end_split[-1]:
                                    endereco['municipio'] = 'Cidade Ocidental'
                                    endereco['end'] = ' '.join(end_split[:-2])
                                elif end_split[-1] == 'BRASILIA':
                                    endereco['municipio'] = 'Brasília'
                                    endereco['end'] = ' '.join(end_split[:-1])
                                else:
                                    endereco['end'] = x.group(1)
                                enderecos.append(endereco)
                            
                            while text[index].strip():
                                print('a')
                                print(text[index])
                                if not re.search(r'^(.*) ([A-Z]{2}) (\d+) *$', text[index]):
                                    print('Endereço  duas linhas')
                                    print(f'{text[index]} {text[index+1]}')
                                    get_endereco(f'{text[index]} {text[index+1]}')
                                    index += 2
                                else:
                                    get_endereco(text[index])
                                    index += 1

                            break
                elif 'BANCO DO BRASIL S/A' in text:
                    credor = Credor.objects.filter(name='BANCO DO BRASIL S/A').first()
                    if not credor:
                        return {'error': 'Credor não cadastrado no banco de dados, rodar init'}, 400
                    # print(text)
                    text = text.split('\n')
                    for i in text:
                        if 'a intimação pessoal' in i:
                            fid = i
                            index = text.index(i)+1
                            # Juntar linhas até "Endereço"
                            while not 'e domiciliado' in text[index]:
                                fid += text[index]
                                index += 1
                                if len(text) <= index:
                                    break

                            # print(text[index])

                            name_list = re.findall(r'([A-Z]+ [ A-Z]+), ', fid)
                            cpf_list = re.findall(r'CPF nº ([\d]+[\.\-\d]*)', fid)
                            if not name_list:
                                return {'error': 'Nenhum fiduciante identificado'}, 400
                            if len(name_list) != len(cpf_list):
                                ignore.append(itm.cod)
                                # return {'error': f'{itm.cod} | Quantidade de Nome não bate com a quantidade de CPF'}, 400
                                # print(f'{itm.cod} | Quantidade de Nome não bate com a quantidade de CPF')
                                break

                            for j in range(0, len(name_list)):
                                pessoa = {
                                    'name': name_list[j],
                                    'cpf': re.sub('\D', '', cpf_list[j]),
                                }
                                ### Buscar estado civil
                                # print(fid)
                                # # Duas pessoas casadas
                                # ADEMILSON DOS SANTOS SAMPAIO, supervisor, inspetor e agente de compras, CI nº 6111392-SSP/GO, CPF nº 055.650.531-02 e sua mulher THAIS RODRIGUES SILVA, do lar, CI nº 6534269-SSP/GO, CPF nº 706.027.991-12, ambos brasileiros, casados sob o regime da comunhão parcial de bens,
                                # x = re.search(r'.*: ([A-z]+[ A-z]*) - cpf (\d+), (\w+) .* comunhão [ a-z]+, ([A-z]+[ A-z]*) - cpf (\d+) *$', pstring)
                                # estcivil = re.search(rf'{p[1]}, (\w+)', fid) or re.search(r'.* - cpf (\d+) *$', fid)
                                # if estcivil:
                                #     pessoa['estcivil'] = estcivil.group(1)
                                pessoas.append(pessoa)

                            # Matrícula
                            while not ' Matrícula nº ' in text[index]:
                                index += 1
                            mat = re.search(r' Matrícula nº ([\.\d]+) ', text[index])
                            if not mat:
                                return {'error': 'Matrícula não encontrada'}, 400
                            matricula = re.sub('\D', '', mat.group(1))

                            # end = text[index]
                            # while not 'em decorrência' in text[index]:
                            #     index += 1
                            #     end += text[index]

                            # print(end)

                            while not '02. ' in text[index]:
                                index += 1
                            index += 1

                            end = text[index]
                            while text[index].strip():
                                end += text[index]
                                index += 1

                            # print(end)
                            x = re.search(r' situado [a-z]{2} (.+), ([ A-z]+)/([A-Z]{2}), CEP ([\d\-]+)', end)
                            if not x:
                                return {'error': 'Endereço inválido'}, 400
                            endereco = {
                                'end': x.group(1),''
                                'municipio': x.group(2),
                                'estado': x.group(3),
                                'cep': re.sub('\D', '', x.group(4)),
                            }

                            #     if end_split[-2] == 'CIDADE' and 'OCIDENT' in end_split[-1]:
                            #         endereco['municipio'] = 'Cidade Ocidental'
                            #         endereco['end'] = ' '.join(end_split[:-2])
                            #     elif end_split[-1] == 'BRASILIA':
                            #         endereco['municipio'] = 'Brasília'
                            #         endereco['end'] = ' '.join(end_split[:-1])
                            #     else:
                            #         endereco['end'] = x.group(1)
                            #     enderecos.append(endereco)
                            break
                        # print(i)
        if not credor:
            ignore.append(itm.cod)
            # return {'error': f'Não foi possível extrair as informações dos arquivos'}, 400
            print(f'{itm.cod} | Não foi possível extrair as informações dos arquivos')
            continue
        if len(pessoas) == 0:
            ignore.append(itm.cod)
            # return {'error': f'{itm.cod} | Pessoas não identificadas'}, 400
            print(f'{itm.cod} | Pessoas não identificadas')
            continue
        if len(enderecos) == 0:
            ignore.append(itm.cod)
            # return {'error': f'{itm.cod} | Endereços não identificados'}, 400
            print(f'{itm.cod} | Endereços não identificados')
            continue

        if len(pessoas) != len(itm.pessoas):
            return f'{len(itm.pessoas)} pessoas na intimacao\n{len(pessoas)} no arquivo'

        # Apagar Devedores
        for p in itm.pessoas:
            p.delete()
        itm.pessoas = []
        # Criar Devedores
        for i in pessoas:
            devedor = Devedor(**i).save()
            itm.pessoas.append(devedor.id)
        if svc:
            svc.mat = matricula
            svc.save()
        else:
            itm.mat = matricula
        itm.credor = credor
        itm.enderecos = enderecos
        itm.save()
        # return 'nha'
    return 'ok'

@bp.get('/') # Get Intimações
@login_required
@check_roles(['itm', 'fin'])
def get():
    itm = Intimacao.objects.filter(func=current_user.id, orcado=None).first()
    if itm:
        return {
            'result': itm.to_dict(),
            'prot_values': prot_values,
            'itm_values': get_itm_values(itm),
        }
    else:
        return {'noresult': '1'}

@bp.get('/list') # Itm List
@login_required
@check_roles(['itm'])
@get_datatable
def list(dt):
    if dt['search']:
        total_filtered = Intimacao.objects().search_text(dt['search']).count()
        list = Intimacao.objects().search_text(dt['search']).skip(dt['start']).limit(dt['length'])
        return {
            'result': [x.to_dict() for x in list],
            'total': total_filtered,
        }

    if dt['filter']:
        match dt['filter']:
            case 'created':
                total_filtered = Intimacao.objects().count()
                list = Intimacao.objects().order_by('-timestamp').skip(dt['start']).limit(dt['length'])
                return {
                    'result': [x.to_dict() for x in list],
                    'total': total_filtered,
                }
            case 'Edital':
                itms = Intimacao.objects.filter(s_edital=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Publicar':
                itms = Intimacao.objects.filter(s_public=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Orçamento':
                itms = Intimacao.objects.filter(s_nopaid=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Protocolar':
                itms = Intimacao.objects.filter(s_noprot=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Pendente':
                itms = Intimacao.objects.filter(s_protpend=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Minuta':
                itms = Intimacao.objects.filter(s_minuta=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Correção':
                itms = Intimacao.objects.filter(s_fix=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Assinar':
                itms = Intimacao.objects.filter(s_nosign=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Imprimir':
                itms = Intimacao.objects.filter(s_noprint=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Visita-1':
                itms = Intimacao.objects.filter(s_visit1=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Visita-2':
                itms = Intimacao.objects.filter(s_visit2=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Visita-3':
                itms = Intimacao.objects.filter(s_visit3=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Diligência':
                itms = Intimacao.objects.filter(s_nodili=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case 'Decurso':
                itms = Intimacao.objects.filter(s_nodecu=True)
                result = [x.to_dict() for x in itms.order_by('-timestamp').skip(dt['start']).limit(dt['length'])]
                total = itms.count()
                return {
                    'result': result,
                    'total': total,
                }
            case _:
                abort(400)

    total_filtered = Intimacao.objects().count()
    list = Intimacao.objects().order_by('name').skip(dt['start']).limit(dt['length'])
    return {
        'result': [x.to_info() for x in list],
        'total': total_filtered,
    }

@bp.get('/info') # Get Itm Info
@login_required
@check_roles(['itm', 'fin'])
def get_info():
    id = request.args.get('id')
    if not (id and len(id) == 24):
        abort(400)
    itm = Intimacao.objects.get_or_404(id=id)

    to_send = get_itm_values(itm)
    to_send['result'] = itm.to_info()
    to_send['prot_values'] = prot_values
    return to_send

@bp.get('/file') # Get Itm File
@login_required
@check_roles(['itm'])
def get_file():
    id = request.args.get('id')
    if not id or len(id) != 24:
        abort(400)
    file = File.objects.get_or_404(id=id)
    if not (file.itm or (file.service and file.service.intimacao)):
        abort(403)

    # if file.content_type == 'application/pkcs7-signature':
    #     content_info: cms.ContentInfo = cms.ContentInfo.load(file.file.read())
    #     signed_data: cms.SignedData = content_info['content']
    #     pdf_data = signed_data['encap_content_info']['content'].native
    #     buffer = BytesIO()
    #     buffer.write(pdf_data)
    #     buffer.seek(0)
    #     return send_file(
    #         buffer,
    #         mimetype='application/pdf',
    #         # as_attachment=True,
    #         # download_name=f'{file.name}.pdf',
    #         # direct_passthrough=True,
    #     )
    return send_file(
        file.file,
        mimetype=file.content_type,
        # as_attachment=True,
        # download_name=fname,
    )

@bp.get('/status') # Get Graph
@login_required
@check_roles(['itm', 'fin'])
def get_status():
    edital = Intimacao.objects(s_edital=True).count()
    nopaid = Intimacao.objects(s_nopaid=True).count()
    noprot = Intimacao.objects(s_noprot=True).count()
    protpend = Intimacao.objects(s_protpend=True).count()
    minuta = Intimacao.objects(s_minuta=True).count()
    fix = Intimacao.objects(s_fix=True).count()
    nosign = Intimacao.objects(s_nosign=True).count()
    noprint = Intimacao.objects(s_noprint=True).count()
    v1 = Intimacao.objects(s_visit1=True).count()
    v2 = Intimacao.objects(s_visit2=True).count()
    v3 = Intimacao.objects(s_visit3=True).count()
    nodili = Intimacao.objects(s_nodili=True).count()
    nodecu = Intimacao.objects(s_nodecu=True).count()
    public = Intimacao.objects(s_public=True).count()

    return {'result': [
        ('Orçamento', nopaid),
        ('Protocolar', noprot),
        ('Pendente', protpend),
        ('Minuta', minuta),
        ('Correção', fix),
        ('Assinar', nosign),
        ('Imprimir', noprint),
        ('Visita-1', v1),
        ('Visita-2', v2),
        ('Visita-3', v3),
        ('Diligência', nodili),
        ('Edital', edital),
        ('Publicar', public),
        ('Decurso', nodecu),
    ]}

@bp.get('/search') # Search Itm
@login_required
@check_roles(['itm'])
@get_roles
def search(roles):
    text = request.args.get('text')
    text = text.strip().upper()
    if not text:
        return {'result': []}
    result = Intimacao.objects.search_text(text).order_by('$text_score')
    return {'result': [x.to_list() for x in result]}


    # fromdate = tz.localize(datetime.strptime(f'{request.args.get("from", str(datetime.now(tz).date()))} 00', '%Y-%m-%d %H')).astimezone(pytz.utc).timestamp()
    # enddate = tz.localize(datetime.strptime(f'{request.args.get("end", str(datetime.now(tz).date()))} 23:59:59', '%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc).timestamp()
    # if enddate and not fromdate:
    #     return {'error': 'Selecione a data inicial.'}, 400

    prots = {}

    ### Atendimentos
    result = {
        'name': current_user.name,
        'attends': [],
        # 'itms': [],
        'payments': {},
        'services': [],
    }

    for a in Attend.objects(func=current_user.id, end__gt=fromdate, end__lt=enddate):
        attend = {
            'id': str(a.id),

            'name': a.user.name,
            'cpf': a.user.cpfcnpj,
            'end': a.end,
            'email': a.user.email,

            'paid': 0.0,
            'to_pay': 0.0,
            'total': 0.0,
        }
        for p in Payment.objects.filter(attend=a.id, confirmed__ne=None):
            attend['paid'] += p.value
            if total_payments.get(p.type):
                total_payments[p.type] += p.value
            else:
                total_payments[p.type] = p.value
            if result['payments'].get(p.type):
                result['payments'][p.type] += p.value
            else:
                result['payments'][p.type] = p.value

        for s in Service.objects(attend=a):
            attend['total'] += s.total
            attend['to_pay'] += s.paid
        # Uso de Saldo
        saldo_usado = float(attend['to_pay'] - attend['paid'])
        if saldo_usado > 0:
            if total_payments.get('cred'):
                total_payments['cred'] += saldo_usado
            else:
                total_payments['cred'] = saldo_usado
            if result['payments'].get('cred'):
                result['payments']['cred'] += saldo_usado
            else:
                result['payments']['cred'] = saldo_usado
        result['attends'].append(attend)
    users[str(current_user.id)] = result
    return {'result': {
        'total_payments': total_payments,
        'users': users,
    }}



@bp.post('/') # New Intimação
@login_required
@check_roles(['itm'])
@get_json
def post(data):
    cod = data.get('cod')
    prot_date = data.get('prot_date')
    files = data.get('files')
    if not (cod and prot_date and files):
        abort(400)
    if len(cod) != 11:
        return {'error': 'Código inválido'}, 400
    if not len(files) > 1:
        return {'error': 'Mínimo de 2 arquivos'}, 400
    prot_date = tz.localize(datetime.strptime(prot_date, '%Y-%m-%d')).astimezone(pytz.utc).timestamp()

    credor = None
    pessoas = []
    enderecos = []
    devedor_created = []
    endereco_created = []
    files_created = []

    force = data.get('force')
    if force:
        n_pessoas = data.get('pessoas')
        if not (n_pessoas and int(n_pessoas) > 0):
            return {'error': 'Quantidade de pessoas não informada'}, 400
        for i in range(0, int(n_pessoas)):
            pessoas.append({'name': '', 'cpf': ''})
        matricula = None
    else:
        for f in files:
            if credor:
                break
            filename = secure_filename(f['fileName'])
            if not path.splitext(filename)[1].lower() in ['.p7s', '.pdf']:
                return {'error': 'Tipo de arquivo inválido'}, 400
            if not f.get('data'):
                return {'error': 'Tipo de arquivo inválido'}, 400

            content = base64.b64decode(f['data'])
            # Test content type

            bcontent = BytesIO(content)
            # Arquivo p7s
            if f['fileType'] == 'application/pkcs7-signature':
                content_info: cms.ContentInfo = cms.ContentInfo.load(content)
                signed_data: cms.SignedData = content_info['content']

                pdf_data = signed_data['encap_content_info']['content'].native
            elif 'pdf' in f['fileType']:
                pdf_data = bcontent
            else:
                return {'error': f'Arquivo inválido | {filename}'}, 400

            # Ler PDF
            with fitz.open(stream=pdf_data, filetype='pdf') as doc:
                text = doc[0].get_text()
                if 'CAIXA ECONÔMICA FEDERAL - CNPJ' in text:
                    credor = Credor.objects.filter(name='CAIXA ECONÔMICA FEDERAL').first()
                    if not credor:
                        return {'error': 'Credor não cadastrado no banco de dados, rodar init'}, 400
                    text = text.split('\n')
                    for i in text:
                        if 'Fiduciante(s):' in i:
                            fid = i
                            index = text.index(i)+1
                            # Juntar linhas até "Matricula:"
                            while not 'Matrícula' in text[index]:
                                fid += ' '+text[index]
                                index += 1
                                if index == len(text):
                                    return {'error': 'Matrícula não encontrada até o fim do arquivo'}, 400
                            p_list = re.findall(r'([A-z]+[ A-z]*) - cpf (\d+)', fid)
                            if not p_list:
                                return {'error': 'Nenhum fiduciante identificado'}, 400
                            for p in p_list:
                                pessoa = {
                                    'name': p[0],
                                    'cpf': p[1][3:] if len(p[1]) ==  14 and p[1].startswith('000') else p[1],
                                }
                                ### Buscar estado civil
                                # # Duas pessoas casadas
                                # x = re.search(r'.*: ([A-z]+[ A-z]*) - cpf (\d+), (\w+) .* comunhão [ a-z]+, ([A-z]+[ A-z]*) - cpf (\d+) *$', pstring)
                                # estcivil = re.search(rf'{p[1]}, (\w+)', fid) or re.search(r'.* - cpf (\d+) *$', fid)
                                # if estcivil:
                                #     pessoa['estcivil'] = estcivil.group(1)
                                pessoas.append(pessoa)

                            # Matrícula
                            x = re.search(r'^Matrícula\(?s?\)?:? ([\d\.]+) *$', text[index])
                            if x:
                                matricula = re.sub('\D', '', x.group(1))
                            else:
                                # return {'error': 'Matrícula não encontrada'}, 400
                                matricula = '0'
                            index += 2

                            # Endereços
                            while not 'demais endereços que estiverem registrados' in text[index]:
                                index += 1
                            if not 'demais endereços que estiverem registrados' in text[index]:
                                return {'error': 'Área de endereços não encontrada'}, 400
                            index += 1
                            def get_end_line(text_line):
                                x = re.search(r'^(.*) ([A-Z]{2})[CEP, ]? (\d+) *$', text_line)
                                if not x:
                                    return 9
                                endereco = {
                                    'cep': x.group(3),
                                    'estado': x.group(2),
                                }
                                end_split = x.group(1).split(' ')
                                if end_split[-2] == 'CIDADE' and 'OCIDENT' in end_split[-1]:
                                    endereco['municipio'] = 'Cidade Ocidental'
                                    endereco['end'] = ' '.join(end_split[:-2])
                                elif end_split[-1] == 'BRASILIA':
                                    endereco['municipio'] = 'Brasília'
                                    endereco['end'] = ' '.join(end_split[:-1])
                                else:
                                    endereco['end'] = x.group(1)
                                enderecos.append(endereco)
                                return 0

                            result = get_end_line(text[index])
                            if result == 9:
                                result = get_end_line(f'{text[index]} {text[index+1]}')
                                if result == 9:
                                    return {'noresult': 'Endereço não identificado'}, 400
                                index += 1

                            index += 1
                            while len(text[index]) > 5:
                                result = get_end_line(text[index])
                                if result == 9:
                                    result = get_end_line(f'{text[index]} {text[index+1]}')
                                    if result == 9:
                                        return {'noresult': 'Endereço não identificado'}, 400
                                    index += 1

                                index += 1
                            break
                elif 'BANCO DO BRASIL S/A' in text:
                    return {'noresult': 'Arquivo não identificado'}, 400

                    # with open ('app/teste.pdf', 'wb') as f:
                    #     f.write(pdf_data)
                    credor = Credor.objects.filter(name='BANCO DO BRASIL S/A').first()
                    if not credor:
                        return {'error': 'Credor não cadastrado no banco de dados, rodar init'}, 400

                    print(text)

                    text = text.split('\n')
                    for i in text:
                        # print(i)
                        if 'a intimação pessoal' in i:
                            fid = i
                            index = text.index(i)+1
                            # Juntar linhas até "Endereço"
                            while not 'e domiciliado' in text[index]:
                                fid += text[index]
                                index += 1
                            # print(text[index])

                            name_list = re.findall(r'([A-Z]+ [ A-Z]+), ', fid)
                            cpf_list = re.findall(r'CPF nº ([\d]+[\.\-\d]*)', fid)
                            if not name_list:
                                return {'error': 'Nenhum fiduciante identificado'}, 400
                            if len(name_list) != len(cpf_list):
                                return {'error': 'Quantidade de Nome não bate com a quantidade de CPF'}, 400

                            for j in range(0, len(name_list)):
                                pessoa = {
                                    'name': name_list[j],
                                    'cpf': re.sub('\D', '', cpf_list[j]),
                                }
                                ### Buscar estado civil
                                # print(fid)
                                # # Duas pessoas casadas
                                # ADEMILSON DOS SANTOS SAMPAIO, supervisor, inspetor e agente de compras, CI nº 6111392-SSP/GO, CPF nº 055.650.531-02 e sua mulher THAIS RODRIGUES SILVA, do lar, CI nº 6534269-SSP/GO, CPF nº 706.027.991-12, ambos brasileiros, casados sob o regime da comunhão parcial de bens,
                                # x = re.search(r'.*: ([A-z]+[ A-z]*) - cpf (\d+), (\w+) .* comunhão [ a-z]+, ([A-z]+[ A-z]*) - cpf (\d+) *$', pstring)
                                # estcivil = re.search(rf'{p[1]}, (\w+)', fid) or re.search(r'.* - cpf (\d+) *$', fid)
                                # if estcivil:
                                #     pessoa['estcivil'] = estcivil.group(1)
                                pessoas.append(pessoa)

                            print(pessoas)


                            # Matrícula
                            while not ' Matrícula nº ' in text[index]:
                                index += 1
                            mat = re.search(r' Matrícula nº ([\.\d]+) ', text[index])
                            if not mat:
                                return {'error': 'Matrícula não encontrada'}, 400
                            matricula = re.sub('\D', '', mat.group(1))

                            print(matricula)

                            # end = text[index]
                            # while not 'em decorrência' in text[index]:
                            #     index += 1
                            #     end += text[index]

                            # print(end)

                            while not '02. ' in text[index]:
                                index += 1
                            index += 1

                            end = text[index]
                            while text[index].strip():
                                end += text[index]
                                index += 1

                            # print(end)
                            x = re.search(r' situado [a-z]{2} (.+), ([ A-z]+)/([A-Z]{2}), CEP ([\d\-]+)', end)
                            if not x:
                                return {'error': 'Endereço inválido'}, 400
                            endereco = {
                                'end': x.group(1),
                                'municipio': x.group(2),
                                'estado': x.group(3),
                                'cep': re.sub('\D', '', x.group(4)),
                            }
                            for z in endereco:
                                print(f'{z}: {endereco[z]}\n')

                            # def get_endereco(estring):
                            #     x = re.search(r'^(.*) ([A-Z]{2}) (\d+) *$', estring)
                            #     if not x:
                            #         print(estring)
                            #         return {'error': 'Endereço inválido'}, 400
                            #     endereco = {
                            #         'cep': x.group(3),
                            #         'estado': x.group(2),
                            #     }
                            #     end_split = x.group(1).split(' ')
                            #     if end_split[-2] == 'CIDADE' and 'OCIDENT' in end_split[-1]:
                            #         endereco['municipio'] = 'Cidade Ocidental'
                            #         endereco['end'] = ' '.join(end_split[:-2])
                            #     elif end_split[-1] == 'BRASILIA':
                            #         endereco['municipio'] = 'Brasília'
                            #         endereco['end'] = ' '.join(end_split[:-1])
                            #     else:
                            #         endereco['end'] = x.group(1)
                            #     enderecos.append(endereco)
                            # get_endereco(text[index])
                            # index += 1
                            # while text[index].strip():
                            #     get_endereco(text[index])
                            #     index += 1

                            break
                        # print(i)
        if not credor:
            return {'noresult': 'Não foi possível extrair as informações dos arquivos'}, 400
        if len(pessoas) == 0:
            return {'noresult': 'Pessoas não identificadas'}, 400
        if len(enderecos) == 0:
            return {'noresult': 'Endereços não identificados'}, 400

    # Criar Devedores
    for i in pessoas:
        devedor = Devedor(**i).save()
        devedor_created.append(devedor.id)

    # Criar Endereços
    for e in enderecos:
        new_end = Endereco(**e).save()
        endereco_created.append(new_end.id)


    intimacao = Intimacao(
        func = current_user.id,
        cod = cod.strip().upper(),
        timestamp = datetime.utcnow().timestamp(),
        prot_date = prot_date,
        pessoas = devedor_created,
        enderecos = endereco_created,
        credor = credor,
        mat = matricula,
    )
    try:
        status = 'Intimação'
        intimacao.save()
        
        comment = data.get('comment')
        if comment and comment.strip():
            comment = Event(
                timestamp = datetime.utcnow().timestamp(),
                actor = current_user.id,
                action = 'comment',
                object = 'itm',
                target = {
                    'id': str(intimacao.id),
                    'comment': comment.strip(),
                },
            )

        # Gravar arquivos no banco
        status = 'Files'
        for f in files:
            filename = secure_filename(f['fileName'])
            content = base64.b64decode(f['data'])
            bcontent = BytesIO(content)
            newfile = File(
                user = current_user.id,
                timestamp = datetime.utcnow().timestamp(),
                name = filename,
                content_type = f['fileType'],
                itm = intimacao.id,
            )
            newfile.file.put(bcontent, app='itm', itm=str(intimacao.id), filename=filename, content_type=f['fileType'])
            newfile.save()
            files_created.append(newfile.id)
        return {'result': 'ok'}
    except db.NotUniqueError:
        for i in devedor_created:
            Devedor.objects.get(id=i).delete()
        return {'error': 'Código já cadastrado no sistema'}, 400
    except Exception as e:
        msg = f"{_('Error saving to database')} | {status}"
        notify(msg, e)

        msg = f'Erro criando Intimação:\n{e}'
        for i in devedor_created:
            Devedor.objects.get(id=i).delete()
        for i in files_created:
            File.objects.get(id=i).delete()
        intimacao.delete_all()
        notify(msg, e)
        return {'error': msg}, 400

@bp.post('/orcar') # Orçar Itm
@login_required
@check_roles(['itm'])
@get_json
def orcar(data):
    id = data.get('id')
    if not (id and len(id) == 24):
        abort(400)
    itm = Intimacao.objects.get_or_404(id=id)
    if itm.orcado:
        abort(400)
    payments_created = []
    events_created = []
    try:
        # Pagamento
        status = 'Payment'
        itm_values = get_itm_values(itm)

        payment1 = Payment(
            func=current_user.id,
            timestamp=datetime.utcnow().timestamp(),
            intimacao=itm.id,
            type='onr',
            value=itm_values['total_prenot'],
        )
        payment1.save()
        payments_created.append(str(payment1.id))

        payment2 = Payment(
            func=current_user.id,
            timestamp=datetime.utcnow().timestamp(),
            intimacao=itm.id,
            type='onr',
            value=(itm_values['total']-itm_values['total_prenot']),
        )
        payment2.save()
        payments_created.append(str(payment2.id))

        itm.orcado = datetime.utcnow().timestamp()
        itm.s_nopaid = True

        status = 'Event'
        event = Event(
            timestamp = datetime.utcnow().timestamp(),
            actor = current_user.id,
            action = 'budget',
            object = 'itm',
            target = {
                'id': str(itm.id),
                'value': itm_values['total'],
            },
        )
        event.save()
        events_created.append(str(event.id))

        # Comentário
        comment = data.get('comment')
        if comment and comment.strip():
            status = 'Comment'
            comment = Event(
                timestamp = datetime.utcnow().timestamp(),
                actor = current_user.id,
                action = 'comment',
                object = 'itm',
                target = {
                    'id': str(itm.id),
                    'comment': comment.strip(),
                },
            )
            comment.save()
            events_created.append(str(comment.id))

        itm.save()
        return {'result': str(itm.id)}
    except Exception as e:
        msg = f"{_('Error saving to database')} | {status}"
        notify(msg, e)
        for i in payments_created:
            to_del = Payment.objects.get(id=i)
            if to_del:
                to_del.delete_all()
        for i in events_created:
            to_del = Event.objects.get(id=i)
            if to_del:
                to_del.delete()
        itm.orcado = None
        itm.s_nopaid = None
        itm.save()
        return {'error': msg}, 400

@bp.put('/payment') # Confirm ITM Payment
@login_required
@check_roles(['itm'])
@get_json
def put_payment(data):
    itm = data.get('itm')
    id = data.get('id')
    if not (id and itm):
        return {'error': 'ID e ITM não encontrados'}
    itm = Intimacao.objects.get_or_404(id=itm)
    payment = Payment.objects.get_or_404(id=id, intimacao=itm.id)
    action = data.get('action')
    match action:
        case 'confirm':
            if payment.confirmed:
                return {'error': 'Payment already confirmed'}, 400
            e_created = []
            try:
                event = Event(
                    timestamp = datetime.utcnow().timestamp(),
                    actor = current_user.id,
                    action = 'confirm',
                    object = 'payment',
                    target = payment.to_dict(),
                )
                payment.confirmed = datetime.utcnow().timestamp()

                if payment.func != current_user.id:
                    print(f'func diferente: {payment.func} / {current_user.id}')
                    payment.func = current_user.id

                itm_prot = Service.objects.filter(type='prot', intimacao=itm.id).first()
                if itm_prot:
                    # Já tem Serviço prot
                    to_pay = round(itm_prot.total - itm_prot.paid, 2)
                    if to_pay > 0:
                        # Falta pagar o total do serviço
                        if payment.value >= to_pay:
                            # Auto Pay Service
                            itm_prot.paid = itm_prot.total
                            itm_prot.save()
                            prot_event = Event(
                                timestamp = datetime.utcnow().timestamp(),
                                actor = current_user.id,
                                action = 'pay',
                                object = 'service',
                                target = itm_prot.to_event(),
                            )
                            prot_event.save()
                            e_created.append(str(prot_event.id))
                            if itm_prot.edital:
                               print('itm_prot.edital')
                               payment.intimacao.s_noprot = True 
                            else:
                                print('else itm_prot.edital')
                                payment.intimacao.s_protpend = False
                                payment.intimacao.s_minuta = True
                        else:
                            notify('itm.put_payment', f'Valor do pagamento é menor que o valor da diferença do serviço pendente - ITM {itm.cod}')
                    else:
                        # Prot já pago
                        print('prot pago')
                        certs = Service.objects.filter(type='cert', intimacao=itm.id)
                        if not len(certs) >= len(itm.pessoas):
                            # Ainda falta Diligencia
                            print('falta diligencia')
                else:
                    print('Sem prot')
                    payment.intimacao.s_noprot = True
                payment.intimacao.s_nopaid = False
                payment.intimacao.save()
                payment.save()
                event.save()
                e_created.append(str(event.id))
                return {'result': str(payment.intimacao.id)}
            except Exception as e:
                msg = 'Erro confirmando pagamento'
                notify(msg, e)
                for i in e_created:
                    to_del = Event.objects.get(id=i)
                    if to_del:
                        to_del.delete()
                payment.confirmed = None
                payment.intimacao.s_nopaid = True
                payment.intimacao.s_noprot = None
                payment.intimacao.save()
                payment.save()
                return {'error': msg}, 400
        case _:
            abort(400)
    abort(400)

@bp.post('/service') # Criar Serviço Protocolo
@login_required
@check_roles(['itm'])
@get_json
def post_service(data):
    id = data.get('id')
    if not (id and len(id) == 24):
        abort(400)
    service = data.get('service')
    if not service:
        return {'error': 'Nenhum serviço informado'}, 400
    for i in ['type', 'prot', 'selo', 'nature', 'prot_date']:
        if not service.get(i):
            return {'error': f'Preencha todos o campos "{i}"'}, 400
    if not service['type'] == 'prot':
        return {'error': 'API apenas para criar Protocolo'}, 400

    s_created = []
    e_created = []

    itm = Intimacao.objects.get_or_404(id=id)
    if not (itm.s_noprot or itm.s_protpend):
        return {'error': 'Intimação sem protocolo pendente'}, 400
    itm_values = get_itm_values(itm)
    s_exist = Service.objects.filter(prot=service['prot']).first()
    if s_exist:
        if s_exist and s_exist.intimacao == itm and s_exist.paid == itm_values['total_prenot']:
            # Serviço pago apenas prenot e busca
            credit = round(Payment.objects.filter(intimacao=itm.id, confirmed__ne=None).sum('value'), 2)
            s_value = itm_values['total_prot']
            # Validar saldo
            if credit < s_value - itm_values['total_prenot']:
                notify('Saldo Insuficiente', 'Ao criar o protocolo da intimação')
                return {'error': 'Saldo insuficiente'}, 400
            new_service['total'] = s_value
            new_service['paid'] = s_value
            # Evento
            status = 'Event'
            event = Event(
                timestamp = datetime.utcnow().timestamp(),
                actor = current_user.id,
                action = 'pay',
                object = 'service',
                target = s_exist.to_list(),
            )
            event.save()
            e_created.append(str(event.id))
            itm.s_protpend = False
            itm.s_minuta = True
            itm.save()
        return {'error': f"Protocolo {service['prot']} duplicado"}, 400
    else:

        #! Validar prot_date recebido com "isdate(service[]'prot_date'])"

        prot_date = tz.localize(datetime.strptime(service['prot_date'], '%Y-%m-%d')).astimezone(pytz.utc).timestamp()
        new_service = {
            'timestamp': datetime.utcnow().timestamp(),
            'type': service['type'].strip().lower(),
            'prot': service['prot'].strip().upper(),
            'intimacao': itm.id,
            'selo': service['selo'],
            'nature': service['nature'],
            'prot_date': prot_date,
        }
        # Matrícula da Itm ou do json
        if itm.mat:
            mat = itm.mat
        else:
            mat = service.get('mat')
            if not mat:
                return {'error': f"Matrícula não informada"}, 400
        new_service['mat'] = mat
        credit = round(Payment.objects.filter(intimacao=itm.id, confirmed__ne=None).sum('value'), 2)
        s_value = itm_values['total_prot']

        # Validar saldo
        if credit < itm_values['total_prenot']:
            notify('Saldo Insuficiente', 'Ao criar o protocolo da intimação')
            return {'error': 'Saldo insuficiente'}, 400
        new_service['total'] = s_value
        new_service['paid'] = itm_values['total_prenot']
        try:
            # Cria o serviço no banco
            status = 'Service'
            new_s = Service(**new_service)
            new_s.save()
            s_created.append(str(new_s.id))

            # Evento
            status = 'Event'
            event = Event(
                timestamp = datetime.utcnow().timestamp(),
                actor = current_user.id,
                action = 'create',
                object = 'service',
                target = new_s.to_list(),
            )
            event.save()
            e_created.append(str(event.id))

            # Migrate Files from Itm to Service Prot
            status = 'Files'
            for f in File.objects(itm=itm.id):
                f.service = new_s.id
                f.itm = None
                f.save()
            itm.mat = None
            itm.s_noprot = False
            itm.s_protpend = True
            itm.save()
        except Exception as e:
            msg = f"{_('Error saving to database')} | {status}"
            notify(msg, e)
            for i in s_created:
                to_del = Service.objects.get(id=i)
                if to_del:
                    for f in File.objects(service=s_created.id):
                        f.service = None
                        f.itm = itm.id
                        f.save()
                    itm.mat = new_s.mat
                    itm.save()
                    to_del.delete_all()
            for i in e_created:
                to_del = Event.objects.get(id=i)
                if to_del:
                    to_del.delete()
            itm.s_noprot = True
            itm.s_minuta = None
            itm.save()
            return {'error': msg}, 400
    status = 'Comment'
    comment = data.get('comment')
    if comment and comment.strip():
        comment = Event(
            timestamp = datetime.utcnow().timestamp(),
            actor = current_user.id,
            action = 'comment',
            object = 'itm',
            target = {
                'id': str(itm.id),
                'comment': comment.strip(),
            },
        )
        comment.save()
        e_created.append(str(comment.id))
    return {'result': str(itm.id)}

@bp.put('/minuta') # Alterar Status Minuta
@login_required
@check_roles(['itm', 'itm-sign'])
@get_json
@get_roles
def put_minuta(roles, data):
    id = data.get('id')
    if not (id and len(id) == 24):
        abort(400)
    action = data.get('action')
    if not action:
        return {'error': 'Ação não informada | "action"'}, 400
    svc = Service.objects.get_or_404(type='prot', intimacao=id)
    events_created = []
    if 'itm-sign' in roles:
        if not svc.minuta_pending:
            return {'error': 'Minuta não pendente de assinatura'}, 400
        if action == 'confirm':
            itm = Intimacao.objects.get(id=svc.intimacao.id)
            def mask_cpf(cpf):
                return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
            def mask_estcivil(e, g):
                return current_app.config['EST_CIVIS'][e]['text'].replace('_', 'a') if g == 'f' else current_app.config['EST_CIVIS'][e]['text'].replace('_', 'o')
            devedores = ' e '.join([
                f"{p.name}, inscrit{'a' if p.genero == 'f' else 'o'} no CPF Nº {mask_cpf(p.cpf)}, {mask_estcivil(p.estcivil, p.genero)}" for p in itm.pessoas
            ])
            img_src = get_qrcode(str(itm.id), visita=True)
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None
            }
            pdf = pdfkit.from_string(
                render_template(
                    'itm/info/minuta_pdf.html',
                    svc=svc,
                    prot_date=tz.localize(datetime.fromtimestamp(svc.prot_date)).strftime('%d/%m/%Y'),
                    credor=itm.credor,
                    devedores=devedores,
                    contrato=itm.contr,
                    enderecos=itm.enderecos,
                    img_src=img_src,
                ), options=options
            )
            datenow = datetime.now(tz).strftime("%d/%m/%Y às %H:%M:%S")
            serventia = current_app.config['SERVENTIA']
            cms_signer = signers.SimpleSigner.load(
                serventia['CERT_KEY'], serventia['CERT_CRT'],
                # ca_chain_files=(serventia['CERT_CA'],),
                # key_passphrase=b'secret',
            )
            w = IncrementalPdfFileWriter(BytesIO(pdf))
            append_signature_field(
                w, sig_field_spec=SigFieldSpec(
                    'Signature', box=(180, 40, 420, 80)
                )
            )
            meta = signers.PdfSignatureMetadata(field_name='Signature')
            pdf_signer = signers.PdfSigner(
                # QRStampStyle TextStampStyle
                meta, signer=cms_signer, stamp_style=stamp.TextStampStyle(
                    border_width=1,
                    background_opacity=0.3,
                    # the 'signer' and 'ts' parameters will be interpolated by pyHanko, if present
                    stamp_text='Assinado digitalmente em %(datenow)s\n%(signer)s',
                    text_box_style=text.TextBoxStyle(
                        font=opentype.GlyphAccumulatorFactory('static/font/LeagueSpartan-Bold.ttf')
                    ),
                    background=images.PdfImage('static/img/logo.jpg'),
                ),
            )
            out = pdf_signer.sign_pdf(
                w,
                appearance_text_params={
                    'url': url_for('base.index', _external=True),
                    'datenow': datenow},
                # signers.PdfSignatureMetadata(field_name='Tey tenistico'),
                # signer=cms_signer,
            )

            newfile = File(
                user = current_user.id,
                timestamp = datetime.utcnow().timestamp(),
                name = f'minuta_{svc.prot}_assinada.pdf',
                content_type = 'application/pdf',
                service = svc.id,
                itm = itm.id,
            )
            newfile.file = out
            newfile.save()
            svc.minuta = newfile.id
            svc.minuta_wrong = None
            svc.intimacao.s_noprint = True
            id = str(newfile.id)
        elif action == 'reject':
            values = data.get('values')
            if not values:
                return {'error': 'Selecione os campos incorretos para correção'}, 400
            svc.minuta_wrong = values
            svc.intimacao.s_fix = True
        else:
            return {'error': 'Ação inválida'}, 400
        svc.intimacao.s_nosign = False
        svc.minuta_pending = None
        svc.intimacao.save()
        svc.save()
    else:
        if action == 'pending':
            if svc.minuta_pending:
                return {'error': 'Minuta já está pendente'}, 400
            if svc.minuta:
                return {'error': 'Minuta já finalizada'}, 400
            svc.minuta_pending = datetime.utcnow().timestamp()
            svc.save()
            svc.intimacao.s_minuta = False
            svc.intimacao.s_fix = False
            svc.intimacao.s_nosign = True
            svc.intimacao.save()
        if action == 'print':
            if not svc.minuta:
                return {'error': 'Serviço sem minuta'}, 400
            svc.minuta_printed = datetime.utcnow().timestamp()
            svc.save()
            svc.intimacao.s_noprint = False
            svc.intimacao.s_visit1 = True
            svc.intimacao.save()
    status = 'Event'
    event = Event(
        timestamp = datetime.utcnow().timestamp(),
        actor = current_user.id,
        action = action,
        object = 'minuta',
        target = {'id': str(svc.id)},
    )
    event.save()
    events_created.append(str(event.id))
    return {'result': id}

@bp.post('/minuta') # Gravar dados para Minuta
@login_required
@check_roles(['itm'])
@get_roles
@get_json
def post_minuta(data, roles):
    id = data.get('id')
    if not (id and len(id) == 24):
        abort(400)
    itm = Intimacao.objects.get_or_404(id=id)
    svc = Service.objects.get_or_404(intimacao=itm.id)
    events_created = []
    if ('adm' in roles or 'itm-sign' in roles) and data.get('mat') and data['mat'] != svc.mat:
        event = Event(
            timestamp = datetime.utcnow().timestamp(),
            actor = current_user.id,
            action = 'edit',
            object = 'mat',
            target = {'id': str(svc.id), 'old': svc.mat, 'new': data['mat']},
        )
        svc.mat = data['mat']
        svc.save()
        event.save()
        events_created.append(str(event.id))

    # Credor
    status = 'Credor'
    credor = data.get('credor')
    if not credor:
        return {'error': 'Credor não informado'}, 400
    if isinstance(credor, dict):
        if not (credor.get('name') and credor.get('cnpj') and credor.get('end')):
            return {'error': 'Dados do credor inválidos'}, 400
        credor = {
            'name': credor.get('name').strip().upper(),
            'cnpj': re.sub('\D', '', credor.get('cnpj').strip()),
            'sede': credor.get('end').strip(),
        }
        if len(credor['cnpj']) != 14:
            return {'error': 'CNPJ do credor inválido'}, 400
        if Credor.objects.filter(cnpj=credor['cnpj']).first():
            return {'error': 'CNPJ do credor já cadastrado'}, 400
        the_credor = Credor(**credor)
        the_credor.save()
    else:
        if not len(credor) == 24:
            return {'error': 'Credor inválido'}, 400
        the_credor = Credor.objects.get_or_404(id=credor)
    itm.credor = the_credor

    # Contrato
    contr = data.get('contr')
    if not contr:
        return {'error': 'Dados do contrato não informado'}, 400
    itm.contr = contr

    # Devedores
    for d in data.get('devedores'):
        devedor = Devedor.objects.filter(id=d['id']).first()
        if not devedor:
            return {'error': 'Devedor não encontrado'}, 404
        name = d.get('name')
        cpf = d.get('cpf')
        genero = d.get('genero')
        estcivil = d.get('estcivil')
        if not (name and cpf and estcivil and genero):
            return {'error': 'Preencha todos os campos do devedor'}, 400
        change = False
        if devedor.name != name:
            devedor.name = name
            change = True
        if devedor.cpf != cpf:
            devedor.cpf = cpf
            change = True
        if devedor.genero != genero:
            devedor.genero = genero
            change = True
        if devedor.estcivil != estcivil:
            devedor.estcivil = estcivil
            change = True
        if change:
            devedor.save()

    # Endereços
    for endereco in data.get('enderecos'):
        endid = endereco.get('id')
        if endid and endid != 'new':
            end_obj = Endereco.objects.get(id=endid)
            for i in ['end', 'estado', 'municipio', 'cep']:
                if i == 'estado':
                    exec(f'end_obj.{i} = "{endereco[i].upper()}"')
                else:
                    clean_text = re.sub('"', '', endereco[i])
                    exec(f'end_obj.{i} = "{clean_text}"')
            end_obj.save()
        else:
            new_end = Endereco(**endereco).save()
            itm.enderecos.append(new_end)

    itm.save()

    # File
    files_created = []
    if data.get('files'):
        for f in data['files']:
            filename = secure_filename(f['fileName'])
            content = base64.b64decode(f['data'])
            bcontent = BytesIO(content)
            newfile = File(
                user = current_user.id,
                timestamp = datetime.utcnow().timestamp(),
                name = filename,
                content_type = f['fileType'],
                # itm = itm.id,
                service = svc.id,
            )
            newfile.file.put(bcontent, app='service', prot=str(svc.id), itm=str(itm.id), filename=filename, content_type=f['fileType'])
            newfile.save()
            files_created.append(newfile.id)

    status = 'Event'
    event = Event(
        timestamp = datetime.utcnow().timestamp(),
        actor = current_user.id,
        action = 'edit',
        object = 'minuta',
        target = {'id': str(svc.id)},
    )
    event.save()
    events_created.append(str(event.id))

    status = 'Comment'
    comment = data.get('comment')
    if comment and comment.strip():
        comment = Event(
            timestamp = datetime.utcnow().timestamp(),
            actor = current_user.id,
            action = 'comment',
            object = 'itm',
            target = {
                'id': str(itm.id),
                'comment': comment.strip(),
            },
        )
        comment.save()
        events_created.append(str(comment.id))

    return {'result': str(itm.id), 'credor': str(the_credor.id) if isinstance(credor, dict) else '' }


def update_itm_visitas(id):
    itm = Intimacao.objects.get_or_404(pessoas__contains=id)
    itm.s_nodili = False
    v1 = None
    v2 = None
    v3 = None
    # Endereços e pessoas da Intimação
    enderecos = [str(x.id) for x in itm.enderecos]
    devedores = [str(x.id) for x in itm.pessoas]
    for d in itm.pessoas:
        negativa = True
        if d.intimado:
            devedores.remove(str(d.id))
            if not Service.objects.filter(type='cert', pessoa=d.id).first():
                itm.s_nodili = True
            continue
        # # Todas visitas do Devedor
        # d_results = [x.result for x in Visita.objects(dev=d.id).only('end', 'result')]
        # # Visita "positiva": marca intimado e remove da lista
        # if 'p' in d_results or 'r' in d_results or 'f' in d_results:
        #     d.intimado = True
        #     d.save()
        #     devedores.remove(str(d.id))
        #     if not Service.objects.filter(type='cert', pessoa=d.id).first():
        #         itm.s_nodili = True
        #         itm.save()
        #     continue
        # Endereços
        ends = enderecos.copy()
        for e in enderecos:
            e_results = [x.result for x in Visita.objects(dev=d.id, end=e)]
            # Mudou / Invalido
            if 'm' in e_results or 'd' in e_results or 'i' in e_results:
                ends.remove(e)
                # negativa = False
            elif len(e_results) >= 3:
                ends.remove(e)
                for e in e_results:
                    if e != 'n':
                        negativa = False
            elif len(e_results) == 2:
                v3 = True
                negativa = False
            elif len(e_results) == 1:
                v2 = True
                negativa = False
            elif len(e_results) == 0:
                v1 = True
                negativa = False
        if len(ends) == 0:
            d.intimado = True
            d.save()
            devedores.remove(str(d.id))
            if not Service.objects.filter(type='cert', pessoa=d.id).first():
                if negativa:
                    svc_prot = Service.objects.get_or_404(type='prot', intimacao=itm.id)
                    svc_prot.edital = {'devedor': str(d.id)}
                    svc_prot.save()
                itm.s_nodili = True
            # else:
            #     print('\nServiço de Diligencia ja existente\n')
            # continue
    # Visitas finalizadas
    if len(devedores) == 0:
        # Decurso
        if len(itm.pessoas) == Service.objects.filter(type='cert', intimacao=itm.id, nature=nature_dili).count():
            itm.s_nodili = False
            if not itm.s_edital:
                itm.s_nodecu = True

    itm.s_visit1 = v1
    itm.s_visit2 = v2
    itm.s_visit3 = v3
    itm.save()

@bp.post('/visita') # Nova Visita
@login_required
@check_roles(['itm'])
@get_json
def post_visita(data):
    for i in ['end', 'dev', 'date', 'result']:
        if not i in data:
            abort(400)
    dev = Devedor.objects.get_or_404(id=data['dev'])
    if dev.intimado:
        return {'error': 'Visitas finalizadas para o devedor!'}, 400
    end = Endereco.objects.get_or_404(id=data['end'])
    v_count = Visita.objects.filter(end=end.id, dev=dev.id).count()
    if v_count >= 3: # ! 3:
        return {'error': 'Máximo de visitas atingido para o endereço!'}, 400
    e_results = [x.result for x in Visita.objects(dev=dev.id, end=end.id)]
    # Mudou / Invalido
    if 'm' in e_results or 'd' in e_results or 'i' in e_results:
        return {'error': 'Endereço não aceita mais visitas!'}, 400

    # files_created = []
    events_created = []
    visitas_created = []
    if data['result'] in ['p', 'r', 'f', 'c']:
        dev.intimado = True
        dev.save()
    elif data['result'] in ['m', 'd', 'i', 'n']:
        pass
    else:
        return {'error': 'Resultado da visita inválido!'}, 400
    
    #! Validar dia de cada visita

    status = 'Visita'

    data['date'] = tz.localize(datetime.strptime(data['date'], '%Y-%m-%d_%H:%M')).astimezone(pytz.utc).timestamp()
    data['timestamp'] = datetime.utcnow().timestamp()
    new_visita = Visita(**data).save()
    visitas_created.append(new_visita.id)

    status = 'Event'
    event = Event(
        timestamp = datetime.utcnow().timestamp(),
        actor = current_user.id,
        action = 'create',
        object = 'visita',
        target = {'id': str(end.id), 'visita': new_visita.to_event()},
    )
    event.save()
    events_created.append(str(event.id))


    ### Update Itm Visitas
    update_itm_visitas(dev.id)

    # # File
    # for f in data.get('file') or []:
    #     filename = secure_filename(f['fileName'])
    #     content = base64.b64decode(f['data'])
    #     bcontent = BytesIO(content)
    #     newfile = File(
    #         user = current_user.id,
    #         timestamp = datetime.utcnow().timestamp(),
    #         name = filename,
    #         content_type = f['fileType'],
    #         itm = intimacao.id,
    #     )
    #     newfile.file.put(bcontent, app='service', devedor=data['dev'], filename=filename, content_type=f['fileType'])
    #     newfile.save()
    #     files_created.append(newfile.id)

    return {'result': 'ok'}

@bp.post('/selo') # Gravar Selo edital
@login_required
@check_roles(['itm'])
@get_json
def post_selo(data):
    id = data.get('id')
    svc = data.get('svc')
    selo = data.get('selo')
    if not (id and svc and selo and len(id) == 24):
        abort(400)
    svc = Service.objects.get_or_404(id=svc, intimacao=id, edital__ne=None)
    if svc.edital.get('selo'):
        return {'error': 'Serviço já tem selo de edital gavado'}, 400
    events_created = []
    svc.edital['selo'] = selo
    svc.intimacao.s_public = True
    svc.intimacao.s_noprot = False
    svc.intimacao.save()
    svc.save()
    return {'result': 1}

@bp.post('/edital') # Gravar dados do Edital
@login_required
@check_roles(['itm'])
@get_json
def post_edital(data):
    id = data.get('id')
    svc = data.get('svc')
    if not (id and svc and len(id) == 24):
        abort(400)
    for i in ['dia1', 'dia2', 'dia3', 'files']:
        if not data.get(i):
            return {'error', f'"{i}" obrigatório.'}, 400
    svc = Service.objects.get_or_404(id=svc, intimacao=id, edital__ne=None)
    if not svc.edital.get('selo'):
        return {'error': 'Serviço ainda sem selo de edital'}, 400
    events_created = []

    # File
    files_created = []
    for f in data['files']:
        filename = secure_filename(f['fileName'])
        content = base64.b64decode(f['data'])
        bcontent = BytesIO(content)
        newfile = File(
            user = current_user.id,
            timestamp = datetime.utcnow().timestamp(),
            name = filename,
            content_type = f['fileType'],
            itm = id,
            # service = svc.id,
        )
        newfile.file.put(bcontent, app='edital', prot=str(svc.id), itm=str(svc.intimacao.id), filename=filename, content_type=f['fileType'])
        newfile.save()
        files_created.append(str(newfile.id))
    edital = {
        'dia1': data['dia1'],
        'dia2': data['dia2'],
        'dia3': data['dia3'],
        'files': files_created,
    }

    svc.edital = {**svc.edital, **edital}
    svc.intimacao.s_public = False
    svc.intimacao.s_nodecu = True
    svc.intimacao.save()
    svc.save()
    return {'result': 1}

@bp.post('/cert') # Certidão Diligencia
@login_required
@check_roles(['itm'])
@get_json
def post_dili(data):
    for i in ['cod', 'dev', 'itm', 'file']:
        if not i in data:
            abort(400)
    # Pessoa
    devedor = Devedor.objects.get_or_404(id=data['dev'])
    if not devedor.intimado:
        return {'error': f"Visitas não finalizadas para o devedor"}, 400

    if Service.objects.filter(prot=data['cod']).first():
        return {'error': f"Protocolo nº {data['cod']} já existe"}, 400

    itm = Intimacao.objects.get_or_404(id=data['itm'])
    if not devedor in itm.pessoas:
        return {'error': f"Devedor não encontrado na Intimação"}, 400

    # Validar saldo
    payments = Payment.objects.filter(intimacao=itm.id, confirmed__ne=None)
    credit = round(sum([x.value for x in payments]), 2)
    services = Service.objects.filter(intimacao=itm.id).only('paid')
    spent = round(sum([x.paid for x in services]), 2)
    credit = round(credit - spent, 2)
    s_value = prot_values['cert']
    if credit < s_value:
        notify('Saldo Insuficiente', 'Criando o certidão de diligencia da intimação')
        return {'error': 'Saldo insuficiente'}, 400

    files_created = []
    services_created = []
    events_created = []
    try:
        # Criar serviço Certidao
        new_service = {
            'timestamp': datetime.utcnow().timestamp(),
            'type': 'cert',
            'prot': data['cod'].strip().upper(),
            'intimacao': itm.id,
            'nature': nature_dili,
            'total': s_value,
            'paid': s_value,
            'pessoa': devedor,
        }
        new_s = Service(**new_service)
        new_s.save()
        services_created.append(str(new_s.id))

        # File
        for f in data['file']:
            filename = secure_filename(f['fileName'])
            content = base64.b64decode(f['data'])
            bcontent = BytesIO(content)
            newfile = File(
                user = current_user.id,
                timestamp = datetime.utcnow().timestamp(),
                name = filename,
                content_type = f['fileType'],
                itm = itm.id,
                service = new_s.id,
            )
            newfile.file.put(bcontent, app='service', prot=str(new_s.id), itm=str(itm.id), filename=filename, content_type=f['fileType'])
            newfile.save()
            files_created.append(newfile.id)

        # Evento
        status = 'Event'
        event = Event(
            timestamp = datetime.utcnow().timestamp(),
            actor = current_user.id,
            action = 'create',
            object = 'service',
            target = new_s.to_list(),
        )
        event.save()
        events_created.append(str(event.id))

        status = 'Comment'
        comment = data.get('comment')
        if comment and comment.strip():
            comment = Event(
                timestamp = datetime.utcnow().timestamp(),
                actor = current_user.id,
                action = 'comment',
                object = 'itm',
                target = {
                    'id': str(itm.id),
                    'comment': comment.strip(),
                },
            )
            comment.save()
            events_created.append(str(comment.id))

        itm_prot = Service.objects.get_or_404(intimacao=itm.id, type='prot')
        if itm_prot.edital:
            itm.s_edital = True
        else:
            itm.s_nodecu = True
        itm.s_nodili = False
        itm.save()

        ### Update Itm Visitas
        update_itm_visitas(devedor.id)


        return {'result': 'ok'}
    except Exception as e:
        msg = f"{_('Error saving to database')} | {status}"
        notify(msg, e)
        for i in services_created:
            to_del = Service.objects.get(id=i)
            if to_del:
                for f in File.objects(service=to_del.id):
                    f.service = None
                    f.itm = itm.id
                    f.save()
                itm.mat = new_s.mat
                itm.save()
                to_del.delete_all()
        for i in events_created:
            to_del = Event.objects.get(id=i)
            if to_del:
                to_del.delete()
        itm.s_noprot = True
        itm.s_minuta = None
        itm.save()
        return {'error': msg}, 400

@bp.post('/decur') # Certidão Decurso
@login_required
@check_roles(['itm'])
@get_json
def post_decur(data):
    for i in ['cod', 'itm']:
        if not i in data:
            abort(400)
    if Service.objects.filter(prot=data['cod']).first():
        return {'error': f"Protocolo nº {data['cod']} já existe"}, 400
    itm = Intimacao.objects.get_or_404(id=data['itm'])

    if not itm.s_nodecu:
        return {'error': f"Intimação não pendente de Decurso"}, 400

    # Validar saldo
    payments = Payment.objects.filter(intimacao=itm.id)
    credit = round(sum([x.value if x.confirmed else 0 for x in payments]), 2)
    s_value = prot_values['cert']
    if credit < s_value:
        notify('Saldo Insuficiente', 'Criando o protocolo da intimação')
        return {'error': 'Saldo insuficiente'}, 400

    services_created = []
    events_created = []
    try:
        # Criar serviço Certidao
        new_service = {
            'timestamp': datetime.utcnow().timestamp(),
            'type': 'cert',
            'prot': data['cod'].strip().upper(),
            'intimacao': itm.id,
            'nature': nature_decur,
            'total': s_value,
            'paid': s_value,
        }
        new_s = Service(**new_service)
        new_s.save()
        services_created.append(str(new_s.id))

        itm.s_ended = True
        itm.s_nodecu = False
        itm.save()
        # Evento
        status = 'Event'
        event = Event(
            timestamp = datetime.utcnow().timestamp(),
            actor = current_user.id,
            action = 'create',
            object = 'service',
            target = new_s.to_list(),
        )
        event.save()
        events_created.append(str(event.id))

        return {'result': 'ok'}
    except Exception as e:
        msg = f"{_('Error saving to database')} | {status}"
        notify(msg, e)
        for i in services_created:
            to_del = Service.objects.get(id=i)
            if to_del:
                for f in File.objects(service=to_del.id):
                    f.service = None
                    f.itm = itm.id
                    f.save()
                itm.mat = new_s.mat
                itm.save()
                to_del.delete_all()
        for i in events_created:
            to_del = Event.objects.get(id=i)
            if to_del:
                to_del.delete()
        itm.s_noprot = True
        itm.s_minuta = None
        itm.save()
        return {'error': msg}, 400


@bp.put('/')
@login_required
@check_roles(['itm'])
@get_json
def put_itm(data):
    id = data.get('id')
    action = data.get('action')
    if not (id and len(id) == 24 and action):
        abort(400)
    match data['action']:
        case 'edital':
            itm = Intimacao.objects.get_or_404(id=id, s_edital=True)
            svc = Service.objects.get_or_404(intimacao=itm.id, type='prot')
            new_p = Payment(
                func = current_user.id,
                intimacao = id,
                timestamp = datetime.utcnow().timestamp(),
                type = 'onr',
                value = prot_values['edital'],
            ).save()
            svc.total = round(prot_values['edital'] + svc.total, 2)
            svc.save()
            # itm.orcado = datetime.utcnow().timestamp()
            itm.s_nopaid = True
            itm.s_edital = False

            status = 'Event'
            event = Event(
                timestamp = datetime.utcnow().timestamp(),
                actor = current_user.id,
                action = 'edital',
                object = 'itm',
                target = {
                    'id': str(itm.id),
                    'value': new_p.value,
                },
            )
            event.save()

            itm.save()

            return {'result': 1}
        case _:
            abort(400)

    return {'result': 1}


@bp.delete('/') # Delete Intimacao
@login_required
@check_roles(['itm', 'adm'])
@get_roles
@get_json
def delete(data, roles):
    id = data.get('id')
    if not (id and len(id) == 24):
        abort(400)
    itm = Intimacao.objects.get_or_404(id=id)
    payments = Payment.objects(intimacao=itm.id)

    if len(payments) == 0:
        itm.delete_all()
        return {'result': 'deleted'}

    if not 'adm' in roles:
        abort(403)

    for i in payments:
        if i.confirmed:
            return {'error': 'Intimação com orçamento pago'}, 400
    try:
        itm.delete_all()
        return {'result': 'deleted'}
    except Exception as e:
        msg = _('Error saving to database')
        notify(msg, e)
        return {'error': msg}, 400

@bp.delete('/end') # Delete Endereço
@login_required
@check_roles(['itm'])
@get_json
def del_end(data):
    id = data.get('id')
    end = data.get('end')
    if not (id and len(id) == 24 and end):
        abort(400)
    itm = Intimacao.objects.get_or_404(id=id)
    endereco = Endereco.objects.get_or_404(id=end)
    itm.enderecos.remove(endereco)
    itm.save()
    endereco.delete()
    return {'result': 'ok'}

@bp.delete('/visita') # Delete Visita
@login_required
@get_json
def delete_visita(data):
    for i in ['id', 'dev']:
        if not i in data:
            return {'error': f'Parâmetro "{i}" obrigatório'}, 400
    dev = Devedor.objects.get_or_404(id=data['dev'])
    vst = Visita.objects.get_or_404(id=data['id'], dev=data['dev'])

    event = Event(
        timestamp = datetime.now(timezone.utc).timestamp(),
        actor = current_user.id,
        action = 'delete',
        object = 'visita',
        target = {'id': str(vst.end.id), 'visita': vst.to_event()},
    )

    vst.delete()
    dev.intimado = False
    dev.save()
    update_itm_visitas(dev.id)
    event.save()

    return {'result': 1}

@bp.delete('/cert') # Delete Diligencia
@login_required
@get_json
def delete_dili(data):
    for i in ['id', 'itm']:
        if not i in data:
            abort(400)
    itm = Intimacao.objects.get_or_404(id=data['itm'])
    svc = Service.objects.get_or_404(id=data['id'], intimacao=data['itm'])
    devedor = svc.pessoa.id
    svc.delete_all()
    event = Event(
        timestamp = datetime.now(timezone.utc).timestamp(),
        actor = current_user.id,
        action = 'delete',
        object = 'visita',
        target = {'id': str(vst.end.id), 'visita': vst.to_event()},
    )
    itm.s_edital = False
    itm.s_nodecu = False
    itm.s_nodili = True
    itm.save()
    update_itm_visitas(devedor)
    return {'result': 1}


# Gravar Commentário da Itm
@bp.post('/comment') # Gravar Itm
@login_required
@check_roles(['itm'])
@get_json
def post_comment(data):

    # print(data)

    id = data.get('id')
    if not (id and len(id) == 24):
        abort(400)
    itm = Intimacao.objects.get_or_404(id=id)

    # events_created = []
    # services_created = []
    # visits_created = []

    comment = data.get('comment')
    if comment and comment.strip():
        status = 'Comment'
        comment = Event(
            timestamp = datetime.utcnow().timestamp(),
            actor = current_user.id,
            action = 'comment',
            object = 'itm',
            target = {
                'id': str(itm.id),
                'comment': comment.strip(),
            },
        )
        comment.save()
        events_created.append(str(comment.id))

    return {'result': str(itm.id)}

    # # Minutas
    # minuta = data.get('minuta')
    # if minuta:
    #     action = 'minuta'
    #     status = 'Minuta'
    #     service = Service.objects.filter(prot=minuta['prot'], intimacao=itm.id).first()
    #     if not service:
    #         return {'error': 'Serviço da Minuta não encontrado'}, 400
        
    #     # if not path.splitext(filename)[1].lower() in ['.jpg', '.jpeg', '.png', '.gif']:
    #     #     return {'error': 'Tipo de arquivo inválido'}, 400
    #     filename = secure_filename(minuta['fileName'])
    #     content = base64.b64decode(minuta['data'])
    #     bcontent = BytesIO(content)
    #     newfile = File(
    #         user = current_user.id,
    #         timestamp = datetime.utcnow().timestamp(),
    #         name = filename,
    #         content_type = minuta['fileType'],
    #         service = service.id,
    #         # itm = itm.id,
    #     )
    #     newfile.file.put(bcontent, app='itm', service=str(service.id), filename=filename, content_type=minuta['fileType'])
    #     newfile.save()
    #     files_created.append(newfile.id)

    #     service.minuta = newfile.id
    #     # service.files.append(newfile.id)
    #     service.save()

    #     # Gravar evento EDIT SERVICE com to_dict antigo

    # # Visitas das Diligencias
    # pessoas = data.get('pessoas')
    # if pessoas and len(pessoas) > 0:
    #     action = 'visit'
    #     status = 'Visit'
    #     # Validar
    #     for visita in pessoas:
    #         if not visita.get('cpf'):
    #             return {'error': 'CPF Obrigatório'}, 400
    #         if not verify_cpfcnpj(visita['cpf']):
    #             return {'error': 'CPF Inválido'}, 400
    #         if not visita.get('result') in ['p', 'n', 'r', 'f']:
    #             return {'error': 'Resultado da diligencia inválido'}, 400
    #         identified = False
    #         for p in itm.pessoas:
    #             # Identificar pelo CPF
    #             if p.cpf and visita.get('cpf') == p.cpf:
    #                 identified = True
    #                 if len(p.visitas) > 2:
    #                     return {'error': 'Máximo de visitas atingido'}, 400
    #         if not identified:
    #             for p in itm.pessoas:
    #                 # Apenas entre os "novos", CPF nem visita anterior
    #                 if p.cpf:
    #                     continue
    #                 # Identificar pelo Estado/Municipio
    #                 if p.estado == visita.get('estado') and p.municipio == visita.get('municipio'):
    #                     identified = True
    #                     if len(p.visitas) > 0:
    #                         return {'error': 'Pessoa com Visita e sem CPF'}, 400
    #         if not identified:
    #             return {'error': 'Pessoa não identificada'}, 400

    # target['files'] = len(files_created)

    # if len(services_created) > 0 or len(payments_created) > 0 or len(visits_created) > 0:
    #     status = 'Event'
    #     event = Event(
    #         timestamp = datetime.utcnow().timestamp(),
    #         actor = current_user.id,
    #         action = action,
    #         object = 'itm',
    #         target = target,
    #     )
    #     event.save()
    #     events_created.append(str(event.id))


    # if len(services_created) > 0:  # or len(visits_created) > 0:
    #     status = 'Event'
    #     event = Event(
    #         timestamp = datetime.utcnow().timestamp(),
    #         actor = current_user.id,
    #         action = 'budget',
    #         object = 'itm',
    #         target = target,
    #     )
    #     event.save()
    #     events_created.append(str(event.id))



    # except Exception as e:
    #     msg = f"{_('Error saving to database')} | {status}"
    #     notify(msg, e)
    #     for i in services_created:
    #         to_del = Service.objects.filter(id=i).first()
    #         if to_del:
    #             to_del.delete()
    #     for i in payments_created:
    #         to_del = Payment.objects.filter(id=i).first()
    #         if to_del:
    #             to_del.delete()
    #     for i in files_created:
    #         to_del = File.objects.get(id=ObjectId(i))
    #         if to_del:
    #             to_del.delete()

    #     # Apagar visitas criadas

    #     for i in events_created:
    #         to_del = Event.objects.filter(id=i).first()
    #         if to_del:
    #             to_del.delete()
    #     return {'error': msg}, 400
    abort(404)
