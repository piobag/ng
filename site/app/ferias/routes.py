import pytz

from flask import request, abort
from flask_login import current_user, login_required

from . import bp, Ferias, verify_ferias
from ..auth import check_roles, get_roles, get_json, notify
from ..base import User

tz = pytz.timezone('America/Sao_Paulo')

@bp.get('/') # Get user ferias
@login_required
@check_roles(['ng'])
def index():
    return {'result': [x.to_dict() \
        for x in Ferias.objects.filter(user=current_user).only(
            'id', 'start', 'end', 'confirmed', 'rejected')]}

@bp.post('/') # New ferias
@login_required
@check_roles(['ng'])
@get_json
@get_roles
def new(roles, data):
    start = data.get('start')
    end = data.get('end')
    if not (start and end):
        return {'error': 'Preencha as datas de início e fim desejadas.'}, 400
    user = data.get('user')
    if user and 'finance' in roles:
        return verify_ferias(User.objects.get_or_404(id=user), start, end)
    else:
        return verify_ferias(current_user, start, end)

@bp.delete('/') # Delete ferias
@login_required
@check_roles(['ng'])
@get_json
def delete(data):
    oid = data.get('delete')
    if not oid or len(oid) < 12:
        abort(400)
    f = Ferias.objects.get_or_404(id=oid)
    try:
        f.delete()
        return {'result': 'deleted'}
    except Exception as e:
        notify(_('Error saving to database'), e)
        return {'error': _('Error saving to database')}, 400

@bp.get('/list') # Get list for Adm/Fin
@login_required
@check_roles(['fin'])
def list():
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 5, type=int)
    filter = request.args.get('filter')
    if not filter:
        return {'error': 'Argumento filter obrigatório'}, 400

    if filter == 'pending':
        total_filtered = Ferias.objects(confirmed=False, rejected=False).count()
        list = Ferias.objects(confirmed=False, rejected=False).skip(start).limit(length).order_by('-timestamp')
    elif filter == 'conflicting':
        conflicts = []
        for f in Ferias.objects(confirmed=False, rejected=False).only('id', 'start', 'end'):
            for i in Ferias.objects(confirmed=True, start__lte=f.start, end__gte=f.start):
                if not i.id in conflicts:
                    conflicts.append(i.id)
            for i in Ferias.objects(confirmed=True, start__lte=f.end, end__gt=f.start):
                if not i.id in conflicts:
                    conflicts.append(i.id)
        total_filtered = Ferias.objects(id__in=conflicts).count()
        list = Ferias.objects(id__in=conflicts).skip(start).limit(length)
    elif filter == 'aproved':
        total_filtered = Ferias.objects(confirmed=True).count()
        list = Ferias.objects(confirmed=True).skip(start).limit(length).order_by('-timestamp')
    else:
        return {'error': 'Filtro inválido'}, 400

    return {
        'ok': 1,
        'list': [x.to_dict() for x in list],
        'total': total_filtered,
    }

@bp.put('/') # Confirm / Reject ferias
@login_required
@check_roles(['fin'])
@get_json
def edit(data):
    if data.get('confirm'):
        f = Ferias.objects.get_or_404(id=data['confirm'])
        f.adm = current_user.id
        f.confirmed = True
        f.rejected = False
    elif data.get('reject'):
        f = Ferias.objects.get_or_404(id=data['reject'])
        f.rejected = True
        f.confirmed = False
    else:
        abort(400)
    f.save()
    f.send_mail()
    return {'result': 'ok'}
