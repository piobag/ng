from . import Attend, Service
import pandas as pd
import re
from ..auth.cpfcnpj import verify_cpfcnpj
from ..base import User, Event
from datetime import datetime, timezone
from mongoengine.errors import ValidationError, NotUniqueError
from pymongo.errors import DuplicateKeyError
from pytz import timezone as pytz_timezone
from flask import jsonify

from flask_login import current_user

def import_xls():
    FILE = 'app/attend/cartas.xlsx'
    df = pd.read_excel(FILE)#, sheet_name=None)
    results = []
    
    # for index, row in df.iterrows():
    #     if pd.notna(row['Apresentante']) and str(row['Apresentante']).strip():
    #         print(f"Linha {index}: Apresentante válido: {row['Apresentante']}")
        
    # return
    for index, row in df.iterrows():
        # if str(row['Apresentante']):
        
        if pd.notna(row.get('Apresentante')) and str(row['Apresentante']).strip():
            start = datetime.now(timezone.utc).timestamp()
            name = str(row['Devedor'])
            # Checar se é um  CPF ou CNPJ Valido
            doc = re.sub('\D', '', row['Documento'])
            if not verify_cpfcnpj(doc):
                # return {'error': _('Invalid CPF')}, 400
                results.append({
                    'line': index,
                    'status': 'error',
                    'name': name,
                    'message': 'Invalid CPF/CNPJ',
                })
                continue
            # Checar se o CPF/CNPJ está cadastrado no sistema
            user = User.objects.filter(cpfcnpj=doc).first()
            if user:
                save = False
                if user.name != name:
                    print(f'Mudando nome de {user.name} para {name}')
                    user.name = name
                    save = True
                if save:
                    user.save()
            else:
            # Cadastrar novos no sistema
                if len(doc) > 11:
                    pj = True
                else:
                    pj = False
                user = User(
                    cpfcnpj=doc,
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
                    end = start
                )
                attend.save()
            except Exception as e:
                # msg = _('Error saving to database')
                # return {'error': msg}, 400
                results.append({
                    'line': index,
                    'status': 'error',
                    'name': name,
                    'message': f'Failed to create Attend: {str(e)}',
                })
                continue
            # Função para converter valores de data para timestamp no horário de Brasília
            def to_timestamp(value):
                brasilia_tz = pytz_timezone("America/Sao_Paulo")  # Define o fuso horário de Brasília
                if pd.isna(value):  # Se o valor for nulo, retorna None
                    return None
                if isinstance(value, datetime):  # Já é um objeto datetime
                    localized_dt = brasilia_tz.localize(value, is_dst=None)
                    return int(localized_dt.timestamp())  # Retorna o timestamp como inteiro
                try:
                    # Converte string para datetime com o formato correto e aplica o fuso horário
                    dt = pd.to_datetime(value, format="%d/%m/%Y")
                    localized_dt = brasilia_tz.localize(dt, is_dst=None)
                    return int(localized_dt.timestamp())  # Retorna o timestamp como inteiro
                except Exception as e:
                    print(f"Erro ao converter a data: {e}")
                    return None  # Retorna None se a conversão falhar

            # Função para garantir que o valor seja uma string
            def to_string(value):
                if pd.isna(value):  # Se o valor for nulo, retorna None
                    return None
                return str(value).strip().upper() if isinstance(value, str) else str(value).strip()
            # Cria um dicionário com os valores convertidos e validados
            service_data = {
                "prot_cod": int(row.get('Protocolo')),
                "attend": attend.id,
                "end_bai": to_string(row.get('Bairro')),
                "end_cep": int(row.get('CEP')),
                "end_cid": to_string(row.get('Cidade')),
                "end_log": to_string(row.get('Endereço')),
                "end_uf": to_string(row.get('UF')),
                "prot_emi": to_timestamp(row.get('Data emissão')),
                "prot_esp": to_string(row.get('Espécie')),
                "prot_num": int(row.get('Número do título')),
                "prot_val": row.get('Saldo'),      # Mantém o valor original se for numérico
                "prot_ven": to_timestamp(row.get('Vencimento')),
                "prot_date": to_timestamp(row.get('Data protocolo')),
                "s_start": True,
                "timestamp": datetime.now(timezone.utc).timestamp(),
            }
            # Remove chaves com valores None
            filtered_data = {key: value for key, value in service_data.items() if value is not None}

            try:
                # Cria a instância usando os dados filtrados
                new_s = Service(**filtered_data)
                # Salva ou processa o objeto criado
                new_s.save()
                results.append({
                    'line': index,
                    'status': 'success',
                    'name': name,
                    'message': 'Service created successfully',
                    'service_id': str(new_s.id),
                })
            except (ValidationError, DuplicateKeyError, NotUniqueError) as e:
                # Deleta o Attend se ocorrer um erro ao salvar o Service
                attend.delete()  # Remove o Attend já salvo
                # print(f"Erro ao validar a linha {index}: {e}")
                # return {'error': _('Failed to create Service'), 'details': str(e)}, 400
                results.append({
                    'line': index,
                    'status': 'error',
                    'name': name,
                    'message': f'Failed to create Service: {str(e)}',
                })
                continue

            # Evento
            event = Event(
                timestamp = datetime.now(timezone.utc).timestamp(),
                actor = current_user.id,
                action = 'create',
                object = 'service',
                target = new_s.to_list(),
            )
            event.save()
        else:
                print(f"Linha {index}: Apresentante vazio ou inválido")
    # Retornar o resumo da operação
    return jsonify(results), 200

        