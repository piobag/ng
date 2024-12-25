
# ###
# from app.attend import Service
# # Atualizar todos Serciços para aparecer no Digit
# for i in Service.objects():
#     print(i.prot)
#     i.update_status()

# ###
# from app.attend import Service
# from app.base import File
# # Vincular Imagens do Edital com Intimação
# for s in Service.objects.only('edital', 'intimacao'):
#     if s.edital and s.edital.get('files'):
#         # print(s.intimacao.id)
#         print(s.edital['files'])
#         for f in s.edital['files']:
#             file = File.objects.get(id=f)
#             if not file.itm:
#                 # print('atualizar')
#                 file.itm = s.intimacao.id
#                 file.save()

# ###
# from app.finance import Devedor
# # Corrigir estado civil e genero dos Devedores
# for d in Devedor.objects():
#     if not d.estcivil:
#         continue
#     cancel = False
#     change = False
#     for e in ['solteir', 'casad', 'viúv', 'viuv', 'separad', 'divorciad', 'união']:
#         if d.estcivil.casefold().startswith(e):
#             gen = d.estcivil.casefold().replace(',', '').replace('(a)', '').split(' ')[0][-1]
#             if not gen in ['a', 'o']:
#                 print(f'Genero inválido: {d.estcivil}')
#                 break
#             if gen == 'o':
#                 gen = 'm'
#             else:
#                 gen = 'f'
#             new_estcivil = e[:3].replace('ú', 'u')
#             if d.estcivil != new_estcivil:
#                 d.estcivil = new_estcivil
#                 change = True
#             if d.genero != gen:
#                 d.genero = gen
#                 change = True
#             if change:
#                 d.save()
#             cancel = True
#             break
#     if not cancel:
#         print(d.estcivil)


###########

# # Service Minuta_Wrong de float para dict
# from mongoengine.connection import get_db

# mongo = get_db()
# svcs = mongo['service']
# for s in svcs.find():
#     if isinstance(s.get('minuta_wrong'), float):
#         svcs.update_one({'_id': s.get('_id')}, {'$set': {'minuta_wrong': []}})

# from app.base import Event
# from app.finance import Payment

# # Func nos pagamentos criados
# for e in Event.objects.filter(action='create', object='payment'):
#     p = Payment.objects.filter(id=e.target['id']).first()
#     if not p:
#         print(e.to_dict())
#         continue
#     if p.func:
#         continue
#     p.func = e.actor
#     p.save()

# for p in Payment.objects.filter(func=None):
#     if p.attend:
#         p.func = p.attend.func
#         p.save()
#     elif p.intimacao:
#         p.func = p.intimacao.func
#         p.save()
#     else:
#         print(f'Pagamento sem attend nem itm: {p.to_dict()}')
#         print(p.user.to_dict())


# from datetime import datetime
# from app.base import Event
# from app.attend import Service

# for i in Event.objects.filter(object='service'):
#     svc = Service.objects.filter(id=i.target['id']).only('attend').first()
#     if not svc:
#         # print('Sem service')
#         # print(i.to_dict())
#         # print(datetime.fromtimestamp(i.timestamp))
#         continue
#     if svc.attend:
#         if not len(i.target['attend']) == 24:
#             print('corrigindo')
#             i.target['attend'] = str(svc.attend.id)
#             i.save()

# ### Corrigir credor cadastrado errado
# from app.attend import Service
# from app.itm import Credor

# credor = Credor.objects.get(id='64c11e28df7185bd45c30066')
# credor.name
# svc = Service.objects.get(prot='94754')
# svc.intimacao.credor = credor
# svc.intimacao.save()

# ### Corrigir Eventos de Service sem attend
# from app.base import Event
# from app.attend import Service

# for i in Event.objects.filter(object='service', target__attend=None):
#     svc = Service.objects.filter(id=i.target['id']).only('attend').first()
#     if not svc:
#         print('Sem service')
#         print(i.to_dict())
#     else:
#         if svc.attend:
#             print('Sem attend no evento')
#             print(str(svc.attend))
#             i.target['attend'] = str(svc.attend)
#             i.save()



# ### Serviços sem timestamp
# from app.attend import Service
# from app.finance import Devol
# for s in Service.objects():
#     if not s.timestamp:
#         print('nha')
#         devol = Devol.objects.filter(service=s.id).first()
#         if not devol:
#             print(f'Service sem timestamp e nao Devol')
#         s.timestamp = devol.timestamp
#         s.save()

# ### Status dos Services
# from app.attend import Service
# for s in Service.objects():
#     s.update_status()



# ### Corrigir merda do Ozeias
# # from pprint import pprint
# from app.itm import Intimacao
# itm = Intimacao.objects.get(cod='IN01079940C')
# # pprint(itm.to_dict())
# # Corrigir devedor duplicado
# from app.finance import Devedor
# dev = Devedor.objects.get(id='655e4c7ecc6526598fca9499')
# # pprint(dev.to_info())
# # Remover devedor da ITM e do banco
# del itm.pessoas[1]
# itm.save()
# dev.delete()
# # Conferir Itm
# # itm = Intimacao.objects.get(cod='IN01079940C')
# # pprint(itm.to_dict())
# # Remover pagamento incorreto
# from app.finance import Payment
# pay = Payment.objects.get(id='655e4c82cc6526598fca94ac')
# pay.delete_all()
# # Alterar evendo de criação do serviço
# from app.base import Event
# ev1 = Event.objects.get(action='budget', target__id=str(itm.id))
# ev1.target['value'] = 430.11
# ev1.save()
# # pprint(ev1.to_dict())
# # Alterar valor do serviço para 237.47
# from app.attend import Service
# svc = Service.objects.get(intimacao='655e4c7ecc6526598fca949e')
# svc.total = 237.47
# svc.paid = 237.47
# svc.save()
# # pprint(svc.to_dict())
# # Editar o evento de pagamento do restante do serviço
# ev2 = Event.objects.get(action='pay', target__id='655e4ef44765b0d2bfe519cd')
# ev2.target['total'] = 237.47
# ev2.save()
# # pprint(ev2.to_dict())


# # Reports - Converter datetime para timestamp
# from datetime import datetime
# from mongoengine.connection import get_db

# mongo = get_db()
# reps = mongo['dev_report']
# for r in reps.find():
#     date = r.get('date')
#     if isinstance(date, datetime):
#         print(date.timestamp())
#         reps.update_one({'_id': r.get('_id')}, {'$set': {'date': date.timestamp()}})





# from app.auth import User

# # Altera usuários com cpfcnpj maior que 11 para PJ
# for u in User.objects():
#   if len(u.cpfcnpj) > 11:
#     if not u.pj:
#       u.pj = True
#       u.save()

# # Mostrar PJ de usuários com cpfcnpj maior que 11
# for u in User.objects():
#   if len(u.cpfcnpj) > 11:
#     print(u.pj)


# from bson.dbref import DBRef
# from pymongo.errors import OperationFailure
# from mongoengine.connection import get_db

# from app.attend import Doc

# mongo = get_db()

# # Corrigir evento fora do padrão
# events = mongo['event']
# for e in events.find():
#     target = e.get('target')
#     if target:
#         attend = target.get('attend')
#         if attend:
#             if isinstance(attend, DBRef):
#                 target['attend'] = str(attend.id)
#                 events.update_one({'_id': e.get('_id')}, {'$set': {'target': target}})
#                 print(target)

# # Apagar index
# index_del = 'prot_1'
# print(f'Apagando index {index_del}')
# print(Doc._get_collection().index_information())
# print(Doc._get_collection().drop_index(index_del))

############

# # from app.fix import delete_ghosts
# from mongoengine.connection import get_db
# from app.base import User

# def delete_ghosts():
#     mongo = get_db()

#     ## Usuários
#     users = mongo['user']

#     # Sem CPF
#     antes_sem = 0
#     antes_com = 0
#     for u in users.find():
#         if u.get('cpfcnpj'):
#             antes_com += 1
#         else:
#             antes_sem += 1

#     # ! Apaga todos sem cpfcnpj !
#     for u in users.find():
#         if not u.get('cpfcnpj'):
#             print(f"deletando {u.get('name')} | \t{u.get('email')}")
#             deleted = users.delete_one({'_id': u.get('_id')})

#     sem = 0
#     com = 0
#     for u in users.find():
#         if u.get('cpfcnpj'):
#             com += 1
#         else:
#             sem += 1

#     print(f'antes com: {antes_com}\nantes sem: {antes_sem}')
#     print(f'depois com: {com}\ndepois sem: {sem}')


#     index_del = 'email_1'
#     print(f'Apagando index {index_del}')

#     print(User._get_collection().index_information())
#     User._get_collection().drop_index(index_del)


#     print(f'Corrigindo CPF duplicado')
#     for u in users.find({'cpfcnpj': '85164640759'}):
#         if not u.get('confirmed_at'):
#             print('deletando aroldo')
#             users.delete_one({'_id': u.get('_id')})
#             continue
#         print(f"name: {u.get('cpfcnpj')}")
#         print(f"name: {u.get('name')}")
#         print(f"email: {u.get('email')}")
#         print(f"tel: {u.get('tel')}")
#         print(f"pj: {u.get('pj')}")
#         print(f"timestamp: {u.get('timestamp')}")
#         print(f"confirmed_at: {u.get('confirmed_at')}\n")






# # Corrigir Boleto criado como Crédito
# from app.attend import Attend
# from app.finance import Payment

# a = Attend.objects.get(id='6480816891ce26a1594c9714')
# for p in Payment.objects.filter(attend=a.id):
#     print(p.to_event())
#     # if p.type == 'cc':
#     #     # Alterar o tipo e desconfirmar
#     #     p.type = 'bol'
#     #     p.confirmed = None
#     #     p.save()
#     #     print(p.to_event())
#     #     break



# import base64
# from io import BytesIO
# import qrcode

# from flask import (
#     url_for,
# )





# ### Remove Index de User
# print(User._get_collection().index_information())
# User._get_collection().drop_index('_cls_1_name_text_email_text')

# ### Index conflict
# for i in ['user']:
#     try:
#         exec(f'{i.title()}.objects()')
#     except OperationFailure as e:
#         coll = mongo[i]
#         x = re.search(r'An equivalent index already exists .+ name: "(\w+)", .*$', str(e))
#         if not x:
#             x = re.search(r'already exists with different options:.* name: "(\w+)",.*$', str(e))
#         if not x:
#             x = re.search(r'found existing text index "(\w+)",.*$', str(e))
#         if x:
#             coll.drop_index(f'{x.group(1)}')
#             print(f'\nIndex "{x.group(1)}" na collection {i} deletado\n')
#         else:
#             print(f'\nUnknow OperationFailure:\n{e}')




# from app.finance import Payment
# from app.itm import Intimacao, Visita
# from app.attend import Service
# for i in Intimacao.objects(orcado__ne=None):
#     if Payment.objects.filter(intimacao=i, confirmed=None).first():
#         # pass
#         # print(f'Itm {i.cod} nao paga')
#         i.s_nopaid = True
#         i.save()
#     else:
#         prot = Service.objects.filter(intimacao=i, type='prot').first()
#         if not prot:
#             # pass
#             # print(f'Itm {i.cod} sem protocolo')
#             i.s_noprot = True
#             i.save()
#         else:
#             if not prot.minuta:
#                 if not prot.minuta_wrong and not prot.minuta_pending:
#                     # pass
#                     # print(f'Itm {i.cod} sem minuta')
#                     i.s_minuta = True
#                     i.save()
#                 elif prot.minuta_wrong:
#                     # Correção - Minuta recusada
#                     # print(f'Itm {i.cod} minuta para correção')
#                     i.s_fix = True
#                     i.save()
#                 else:
#                     # Assinar - Minuta pendente (prot.minuta_pending=true)
#                     # print(f'Itm {i.cod} minuta pendente')
#                     i.s_nosign = True
#                     i.save()
#             else:
#                 if not prot.minuta_printed:
#                     # print(f'Itm {i.cod} minuta para impressão')
#                     i.s_noprint = True
#                     i.save()
#                 else:
#                     # Visitas
#                     v1 = None
#                     v2 = None
#                     v3 = None
#                     # Endereços da Intimação
#                     enderecos = [str(x.id) for x in i.enderecos]
#                     # Pessoas da Intimação
#                     devedores = [str(x.id) for x in i.pessoas]

#                     for d in i.pessoas:
#                         # Todas visitas do Devedor
#                         d_results = [x.result for x in Visita.objects(dev=d.id).only('end', 'result')]
#                         # Devedor "intimado"
#                         if d.intimado:
#                             devedores.remove(str(d.id))
#                             if not Service.objects.filter(type='cert', pessoa=d.id).first():
#                                 i.s_nodili = True
#                                 i.save()
#                             continue
#                         # Visita "positiva": marca intimado e remove da lista
#                         if 'p' in d_results or 'r' in d_results or 'f' in d_results:
#                             d.intimado = True
#                             d.save()
#                             devedores.remove(str(d.id))
#                             if not Service.objects.filter(type='cert', pessoa=d.id).first():
#                                 i.s_nodili = True
#                                 i.save()
#                             continue
#                         # Endereços
#                         ends = enderecos.copy()
#                         for e in enderecos:
#                             e_results = [x.result for x in Visita.objects(dev=d.id, end=e)]
#                             # Mudou / Invalido
#                             if 'm' in e_results or 'd' in e_results or 'i' in e_results:
#                                 ends.remove(e)
#                             elif len(e_results) >= 3:
#                                 ends.remove(e)
#                             elif len(e_results) == 2:
#                                 v3 = True
#                             elif len(e_results) == 1:
#                                 v2 = True
#                             elif len(e_results) == 0:
#                                 v1 = True
#                         if len(ends) == 0:
#                             d.intimado = True
#                             d.save()
#                             devedores.remove(str(d.id))
#                             if not Service.objects.filter(type='cert', pessoa=d.id).first():
#                                 i.s_nodili = True
#                             continue
#                     # Visitas finalizadas
#                     if len(devedores) == 0:
#                         # Decurso
#                         if len(i.pessoas) == len(Service.objects.filter(type='cert', intimacao=i.id)):
#                             i.s_nodili = False
#                             i.s_nodecu = True

#                     i.s_visit1 = v1
#                     i.s_visit2 = v2
#                     i.s_visit3 = v3
#                     i.save()


# ### Marcar todas Naturezas como ativas
# from mongoengine.connection import get_db
# from app.attend import Nature

# mongo = get_db()

# coll = mongo['nature']
# for i in coll.find():
#     if not i.get('enabled'):
#         print(i.get('name'))
#         up = coll.update_one({'_id': i.get('_id')}, {'$set': {
#             'enabled': True,
#         }})


# ### Vincular serviços da Itm no novo campo services dentro da Itm
# from app.attend import Service
# from app.itm import Intimacao
# for i in Intimacao.objects():
#     # print(f'Vinculando Itm {i.cod}')
#     i.services = [x.id for x in Service.objects(intimacao=i.id)]
#     i.save()


# ### Erro Intimação Natureza Não existe
# from mongoengine.connection import get_db
# from app.attend import Service
# # from app.itm import Intimacao
# itm_id = '6451cb4bdcb422dbf9a9f41c'
# svc = Service.objects.get(intimacao=itm_id)

# mongo = get_db()
# coll = mongo['service']
# i = coll.find_one({'_id': svc.id})
# if i.get('nature'):
#     print(i['nature'])
# # print(svc.id)
# # print(svc.nature)
# # print(svc.to_dict())



# ### Naturezas existentes para o Grupo RI
# from app.attend import Nature
# for n in Nature.objects():
#     if not n.group:
#         n.group = 'attend'
#         n.save()



# ### Reverter Aprovação da minuta do Serviço da Intimação
# from datetime import datetime
# from mongoengine.connection import get_db
# import gridfs
# from app.itm import Intimacao
# from app.attend import Service
# from app.base import Event

# itm_cod = 'IN00944054C'
# itm = Intimacao.objects.get(cod=itm_cod)
# svc = Service.objects.get(intimacao=itm.id)

# # fs = gridfs.GridFS(get_db())
# # fs.delete(svc.minuta.file.grid_id)
# # svc.minuta.file.delete()
# # svc.minuta.delete()
# # svc.minuta = None

# svc.minuta_pending = None
# # svc.minuta_pending = datetime.utcnow().timestamp()

# # # Desfazer minuta printed
# # svc.minuta_printed = None

# svc.save()

# itm.credor = None
# itm.save()


# # # Apagar Evento
# # # event = Event.objects.get(action='confirm', object='minuta', target={'id': str(svc.id)})
# # # event.delete()
# # event = Event.objects.get(
# #     action='print',
# #     object = 'minuta',
# #     target = {'id': str(svc.id)},
# # )
# # event.delete()




# ### Ler arquivos da intimação
# from ..itm.routes import read_itm_files
# return read_itm_files()






# from bson.objectid import ObjectId
# from pymongo import MongoClient
# from mongoengine.connection import get_db
# import gridfs
# from  ..attend import Service
# from ..itm import Devedor, Intimacao
# from ..booking import Booking
# from ..finance import Devol

# mongo = get_db()
# fs = gridfs.GridFS(get_db())




# # The fields "{'signed'}" do not exist on the document "File"
# coll = mongo['file']
# for i in coll.find():
#     if i.get('signed'):
#         print(i['signed'])




# # from bson.dbref import DBRef
# from bson.objectid import ObjectId
# # from datetime import datetime

# from mongoengine.connection import get_db
# # from mongoengine.errors import ValidationError
# # import gridfs

# # from app.base import File, Event
# from app.itm import Intimacao
# from app.finance import Endereco, Devedor
# # from app.attend import Service

# mongo = get_db()
# fs = gridfs.GridFS(get_db())
# coll_files = mongo['file']



# # Apagar atributro intimado, enderecos, visitas e externo dos devedores
# coll = mongo['devedor']
# for i in coll.find():
#     up = coll.update_one({'_id': i.get('_id')}, {'$unset': {
#         'intimado': 1,
#         'visitas': 1,
#         'enderecos': 1,
#         'externo': 1,
#     }})

#!! Apagar atributro Role dos users



# # Converter endereços das Itm em objetos no banco
# for itm in coll_itm.find():
#     iends = itm.get('enderecos')
#     if not iends:
#         print(f'Itm sem endereços: {itm.get("cod")}')
#         continue
#     if not isinstance(iends[0], dict):
#         # print(f'Endereços not dict: {itm.get("cod")}')
#         continue
#     new_ends = []
#     for e in iends:
#         nend = Endereco(**e).save()
#         new_ends.append(ObjectId(nend.id))
#     up = coll_itm.update_one({'_id': itm.get('_id')}, {'$set': {'enderecos': new_ends}})    




# # stop = False
# print('Intimaçao com File inválido:')
# for itm in coll_itm.find():
#     iid = itm.get('_id')
#     files = itm.get('files')
#     if files and isinstance(files[0], dict):
#         print(itm.get("cod"))
#         svc = Service.objects.filter(intimacao=iid).first()
#         for f in files:
#             fid = f.get('file')
#             if not fid:
#                 print('ID nao encontrado no Dict')
#                 # stop = True
#                 break
#             ff = fs.find_one({'_id': fid})
#             new_file = File(
#                 file = ff,
#                 name = f.get('name'),
#                 content_type = f.get('content_type'),
#                 user = f.get('user'),
#                 timestamp = f.get('timestamp').timestamp(),
#             )
#             if svc:
#                 new_file.service = svc.id
#             else:
#                 new_file.itm = iid
#             new_file.save()
#     #     if stop:
#     #         break
#     # if stop:
#     #     break

# print('Intimacao sem file')
# for itm in coll_itm.find():
#     iid = itm.get('_id')
#     if not File.objects.filter(itm=iid).first():
#         svc = Service.objects.filter(intimacao=iid).first()
#         if svc:
#             if File.objects.filter(service=svc.id).first():
#                 continue
#         print(f"{itm.get('cod')} sem file")
#         if not itm.get('cod').startswith('IN'):
#             # print('apagando...')
#             Intimacao.objects.get(cod=itm.get('cod')).delete_all()

# #!! Apagar Itm que não comece com IN
# for i in Intimacao.objects():
#     if not i.cod.startswith('IN'):
#         print(f'Itm com nome inválido: {i.cod}')
#         i.delete_all()

# # Remover todas as listas de files das Itm e dos Svc
# coll = mongo['intimacao']
# for i in coll.find():
#     coll.update_one({'_id': i.get('_id')}, {'$unset': {'files': 1}})

# coll = mongo['service']
# for i in coll.find():
#     coll.update_one({'_id': i.get('_id')}, {'$unset': {'files': 1} })

# # Devol de teste sem Prot
# print('Apagando Devol de teste, id 6371c56f0086000e472cc766')
# from app.finance import Devol
# Devol.objects.get(id='6371c56f0086000e472cc766').delete_all()

# # Correção Eventos de Service
# print('Corrigindo Eventos')
# for i in Event.objects(object='service'):
#     # Apagar eventos desnecessários
#     if i.action == 'delete':
#         print(f'delete {i.actor.name} {datetime.fromtimestamp(i.timestamp)}')
#         i.delete()
#         continue
#     # Apagar sem Service
#     svc = Service.objects.filter(id=i.target["id"]).first()
#     if not svc:
#         print(f'no_svc {i.id} {i.actor.name} {datetime.fromtimestamp(i.timestamp)}')
#         i.delete()
#         continue
#     # Apagar sem Itm
#     itmid = i.target['itm']
#     if isinstance(itmid, ObjectId):
#         itmid = str(itmid)
#     else:
#         itmid = str(itmid.id)
#     itm = Intimacao.objects.filter(id=itmid).first()
#     if not itm:
#         print(f'no_itm {i.id} {i.actor.name} {datetime.fromtimestamp(i.timestamp)}')
#         i.delete()
#         continue
#     # Recriar target
#     i.target = svc.to_list()
#     i.save()
