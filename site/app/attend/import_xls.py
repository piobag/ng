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
    df = pd.read_excel(FILE)
    results = []

    def calcular_total(val_input):
        """Calcula o total baseado no valor de entrada."""
        atos = {
            'correio': 18.05,
            'taxa': 16.87,
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
        
        # Função para calcular o valor final
        def calcular_valor(val_input, codigo):
            resultado = {}
            valor_base = 0

            if codigo in atos['faixa']:
                faixas = atos['faixa'][codigo]

                # Encontra o menor limite maior ou igual ao val_input
                limite_mais_proximo = min((limite for limite in faixas if limite >= val_input), default=None)

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

                # Calcula os incrementos e o valor final
            if codigo in ['correio', 'taxa']:
                resultado['fundesp_10'] = 0
                resultado['funemp_3'] = 0
                resultado['fucomp_3'] = 0
                resultado['fepasaj_2'] = 0
                resultado['funproge_2'] = 0
                resultado['fundepeg_1_25'] = 0
                resultado['iss_5'] = 0
                resultado['valor_final'] = valor_base
            else:
                fundesp_10 = round(valor_base * 0.1, 2)
                funemp_3 = round(valor_base * 0.03, 2)
                fucomp_3 = round(valor_base * 0.03, 2)
                fepasaj_2 = round(valor_base * 0.02, 2)
                funproge_2 = round(valor_base * 0.02, 2)
                fundepeg_1_25 = round(valor_base * 0.0125, 2)
                iss_5 = round(valor_base * 0.05, 2)
                resultado['fundesp_10'] = fundesp_10
                resultado['funemp_3'] = funemp_3
                resultado['fucomp_3'] = fucomp_3
                resultado['fepasaj_2'] = fepasaj_2
                resultado['funproge_2'] = funproge_2
                resultado['fundepeg_1_25'] = fundepeg_1_25
                resultado['iss_5'] = iss_5
                resultado['valor_final'] = round(valor_base + fundesp_10 + funemp_3 + fucomp_3 + fepasaj_2 + funproge_2 + fundepeg_1_25 + iss_5, 2)


            return resultado


        # Códigos a serem considerados
        codigos_a_considerar = [
            'correio', 'taxa', 'intimacao', 'cancelamento',
            '3132', '3133', '3134', '3135', '3136', '3137', 
            '3138', '3139', '3140', '3141', '3142', '3143'
        ]

        total_valores_finais = 0  # Acumula o total
        faixa_selecionada = False  # Controla se já encontrou a faixa válida

        # Calcula os valores
        for codigo in codigos_a_considerar:
            if faixa_selecionada and codigo in atos['faixa']:
                break  # Para de iterar após encontrar e calcular a faixa válida

            resultado = calcular_valor(val_input, codigo)

            if resultado is not None:
                # Soma apenas os valores finais dos resultados válidos
                total_valores_finais += resultado['valor_final']

                # Marca a faixa como selecionada
                if codigo in atos['faixa']:
                    faixa_selecionada = True

        # Retorna o total final
        return round(total_valores_finais, 2)



    # return
    for index, row in df.iterrows():
        # if str(row['Apresentante']):
        
        if pd.notna(row.get('Apresentante')) and str(row['Apresentante']).strip() and str(row['Situação'] != 'PENDENTE'):
            if row.get('Situação') == 'PENDENTE':
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
                # Adiciona o cálculo do total
                saldo = row.get('Saldo', 0)
                total_valores_finais = calcular_total(saldo)
                prot_num = to_string(row.get('Número do título', ''))
                numero_tratado = re.sub('\D', '', prot_num)

                # Cria um dicionário com os valores convertidos e validados
                service_data = {
                    "prot_cod": int(row.get('Protocolo')),
                    "attend": attend.id,
                    "end_bai": to_string(row.get('Bairro')),
                    "end_cep": int(row.get('CEP')),
                    "end_cid": to_string(row.get('Cidade')),
                    "end_log": to_string(row.get('Endereço')),
                    "end_uf": to_string(row.get('UF')),
                    "prot_apr": to_string(row.get('Apresentante')),
                    "prot_ced": to_string(row.get('Cedente')),
                    "prot_sac": to_string(row.get('Sacador')),
                    "prot_sac_doc":to_string(re.sub('\D', '', row.get('Documento sacador'))),
                    "prot_emi": to_timestamp(row.get('Data emissão')),
                    "prot_esp": to_string(row.get('Espécie')),
                    "prot_num":  int(numero_tratado),
                    "prot_val": row.get('Saldo'),      # Mantém o valor original se for numérico
                    "prot_ven": to_timestamp(row.get('Vencimento')),
                    "prot_date": to_timestamp(row.get('Data ocorrência')),
                    "prot_tot_c": total_valores_finais,
                    "prot_tot_p": total_valores_finais,
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
                        'saldo': saldo,
                        'total pagar': total_valores_finais,
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



        