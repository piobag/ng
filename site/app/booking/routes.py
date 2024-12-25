from os import getenv
from datetime import datetime, timedelta, time
from datetime import date as Date
from collections import Counter
from importlib import import_module
import pytz

from flask_login import login_required, current_user
from flask import (
    request,
    current_app,
    abort )
from flask_babel import _
from workalendar.america import Brazil
from pandas import date_range
from mongoengine.queryset.visitor import Q

from . import bp, Booking, Blacklist
from ..auth import (
    notify,
    check_roles,
    get_roles,
    get_json,
    RoleBind,
    Role, )
from ..base import User

cal = Brazil()
tz = pytz.timezone('America/Sao_Paulo')



# Return a list of free hours or the func_id if a hour is provided
def check_hour(timestamp, mins, hour=None):
    open = current_app.config['OPEN']
    close = current_app.config['CLOSE']
    freq = current_app.config['FREQ']
    services = current_app.config['BOOKING_SERVICES']
    try:
        day = datetime.fromtimestamp(timestamp)
    except ValueError as e:
        msg = _('Invalid day timestamp')
        notify(msg, str(e))
        return {'error': msg}

    # Schedule to the past
    now = datetime.utcnow().timestamp()
    if hour:
        min_mins = float('inf')
        past = hour
    else:
        past = close
    date = tz.localize(datetime.fromisoformat(f'{str(day.date())} {past}')).astimezone(pytz.utc).timestamp()
    if date < now:
        return {'error': _('Unable to schedule to the past')}

    # Dia útil
    if not cal.is_working_day(day):
        return {'error': _('Selected day is not a working day')}
    for b in Blacklist.objects():
        if timestamp >= datetime.fromtimestamp(b.start).timestamp() \
                and timestamp <= datetime.fromtimestamp(b.end).timestamp():
            return {'error': _('There will be no office on this day')}
    free = []
    # try:
    for r in RoleBind.objects(role=Role.objects.only('id').get(name='attend').id).only('user'):
        if not r.user.lunch or r.user.lunch == '00:00':
            continue
        lunch = tz.localize(datetime.fromisoformat(f'{str(day.date())} {r.user.lunch}')).astimezone(pytz.utc).timestamp()
        bookings = Booking.objects(
                    Q(start__gte=tz.localize(datetime.fromisoformat(f"{str(day.date())} 00:00")).astimezone(pytz.utc).timestamp()) & \
                    Q(start__lte=tz.localize(datetime.fromisoformat(f"{str(day.date())} 23:59")).astimezone(pytz.utc).timestamp()) & \
                    Q(func=r.user.id) ).only('start', 'services')
        if hour:
            hours = [hour]
            func_mins = 0
        else:
            hours = [str(x)[:-3] for x in date_range(open, close, freq=freq).time]
        for h in hours:
            start = tz.localize(datetime.fromisoformat(f'{str(day.date())} {h}')).astimezone(pytz.utc).timestamp()
            # Horario de almoço
            if start >= lunch and start <= lunch + timedelta(minutes=60).total_seconds():
                continue
            if start < lunch and start + timedelta(minutes=mins).total_seconds() >= lunch:
                continue
            # Horario de abertura / fechamento
            if start < tz.localize(datetime.fromisoformat(f"{str(day.date())} {open}")).astimezone(pytz.utc).timestamp():
                continue
            if start + timedelta(minutes=mins).total_seconds() >= tz.localize(datetime.fromisoformat(f"{str(day.date())} {close}")).astimezone(pytz.utc).timestamp():
                continue
            # Conflito com os agendamentos do dia
            if bookings:
                breaked = False
                for b in bookings:
                    b_mins = sum([int(b.services[x]) * services[x]['mins'] for x in b.services])
                    if hour:
                        func_mins += b_mins
                    if b.start >= start and start + timedelta(minutes=mins).total_seconds() >= b.start:
                        breaked = True
                        break
                    elif b.start < start and b.start + timedelta(minutes=b_mins).total_seconds() >= start:
                        breaked = True
                        break
                if breaked: continue
            if not h in free:
                free.append(h)
            if hour and func_mins < min_mins:
                func = r.user.id
                min_mins = func_mins
    if len(free) > 0:
        return {'result': func if hour else free}
    else:
        return {'error': _('Time not available') if hour else _('No time available for selection')}
    # except Exception as e:
    #     notify(_('Error checking booking availability'), e)
    #     return {'error': _('Error checking availability, please try again')}
# Calc Free Hours
@bp.post('/calc')
@login_required
@get_json
def calc(data):
    return check_hour(data['day'], int(data['mins']))

# Get Bookings
@bp.get('/')
@login_required
@get_roles
def index(roles):
    attend = request.args.get('attend', None)
    order = request.args.get('order', 'start')
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 5, type=int)
    search = request.args.get('search')
    
    fromdate = tz.localize(datetime.strptime(f'{request.args.get("from", str(datetime.now(tz).date()))} 00', '%Y-%m-%d %H')).astimezone(pytz.utc).timestamp()
    enddate = tz.localize(datetime.strptime(f'{request.args.get("end", str(datetime.now(tz).date()))} 23:59:59', '%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc).timestamp()
    if enddate and not fromdate:
        return {'error': 'Selecione a data inicial.'}, 400
    if 'adm' in roles:
        if search:
            total_filtered = Booking.objects.search_text(search).count()
            list = Booking.objects.search_text(search).skip(start).\
                        limit(length).order_by(order)
        else:
            total_filtered = Booking.objects(start__gt=fromdate, start__lt=enddate, attend=attend).count()
            list = Booking.objects(start__gt=fromdate, start__lt=enddate, attend=attend).\
                                                            skip(start).limit(length).order_by(order)
        return {
            'result': [booking.to_dict() for booking in list],
            'total_filtered': total_filtered,
            'total': Booking.objects.count(),
        }
    elif 'attend' in roles:
        total_filtered = Booking.objects(func=current_user.id, start__gt=fromdate, start__lt=enddate, attend=attend).count()
        list = Booking.objects(func=current_user.id, start__gt=fromdate, start__lt=enddate, attend=attend).\
                                                                skip(start).limit(length).order_by(order)
        return {
            'result': [booking.to_dict() for booking in list],
            'total_filtered': total_filtered,
            'total': Booking.objects.count(),
        }
    else:
        page = request.args.get('page', 1, type=int)
        day = tz.localize(datetime.fromisoformat(f"{request.args.get('from', datetime.now(tz).date())} 00:00")).astimezone(pytz.utc).timestamp()
        bookings = Booking.objects(user=current_user.id, start__gt=day, attend=None).\
                order_by('start').paginate(page=page, per_page=3)
        next_url = bookings.next_num if bookings.has_next else None
        prev_url = bookings.prev_num if bookings.has_prev else None
        if len(bookings.items) == 0:
            return {'result': '0'}
        return {'result': [b.to_dict() for b in bookings.items],
            'next_url': next_url, 'prev_url': prev_url }

    # filter = request.args.get('filter')
    # match filter:
    #     case 'created':
    #         total_filtered = Intimacao.objects(func=current_user.id, timestamp__gt=fromdate, timestamp__lt=enddate).count()
    #         list = Intimacao.objects(func=current_user.id, timestamp__gt=fromdate, timestamp__lt=enddate).order_by('-timestamp').skip(start).limit(length)
    #         return {
    #             'result': [x.to_dict() for x in list],
    #             'total': total_filtered,
    #         }
    #     case _:
    #         abort(400)
    # search = request.args.get('search')
    # if search:
    #     total_filtered = Intimacao.objects.search_text(search).count()
    #     list = Intimacao.objects.search_text(search).skip(start).limit(length)
    #     return {
    #         'result': [x.to_dict() for x in list],
    #         'total': total_filtered,
    #     }



# New Booking
@bp.post('/')
@login_required
@get_json
def new(data):
    services = current_app.config['BOOKING_SERVICES']
    mins = sum([int(data['services'][x]) * services[x]['mins'] for x in data['services']])
    if mins > 0:
        start = datetime.fromisoformat(f"{data['day']} {data['hour']}").astimezone(pytz.utc).timestamp()
        bks = Booking.objects(user=current_user.id, start__gt=datetime.now(tz).astimezone(pytz.utc).timestamp(), attend=None).only('start', 'services')
        # Maximo de atendimentos por usuario
        if bks.count() >= 3:
            return {'error': _('Maximum appointments per user reached')}, 403
        mins_user = 0
        for b in bks:
            mins_bk = sum([int(b.services[x]) * services[x]['mins'] for x in b.services])
            mins_user += mins_bk
            # Agendamento para o mesmo horário
            if b.start >= start and (datetime.fromtimestamp(start) + timedelta(minutes=mins)).timestamp() >= b.start:
                return {'error': f"{_('Conflict with scheduling for')} {b.start}"}, 403
            elif b.start < start and (datetime.fromtimestamp(b.start) + timedelta(minutes=mins_bk)).timestamp() >= start:
                return {'error': f"{_('Conflict with scheduling for')} {b.start}"}, 403
        # Maximo de 3 horas de atendimento total
        if mins_user > 180:
            return {'error': _('Maximum 3 hours of appointment reached')}, 403
        check_resp = check_hour(start, mins, data['hour'])
        if check_resp.get('result'):
            func = check_resp['result']
        elif check_resp.get('error'):
            return check_resp, 400
        bk = Booking(
            timestamp = datetime.utcnow().timestamp(),
            user=current_user.id,
            func=func,
            start=start,
            name=data['name'].strip().title(),
            services=data['services'],
            obs=data.get('obs') )
        try:
            bk.save()
            try:
                bk.send_mail()
            except Exception as e:
                notify(_('Failed to send booking confirmation email'), e)
            return {'result': _('Service scheduled')}
        except Exception as e:
            notify(_('Error saving to the database'), e)
            return {'error': _('Error saving to the database, please try again')}, 404
    else:
        return {'error': _('No service selected')}, 400


@bp.post('/delete') # Delete Booking
@login_required
@get_roles
@get_json
def delete(data, roles):
    bk = Booking.objects.get_or_404(id=data['id'])
    if (bk.user.id == current_user.id and not bk.attend) or 'adm' in roles:
        bk.send_mail(delete=True)
        return {'result': _('Appointment canceled')}
    else:
        return {'error': _('You cannot cancel this appointment')}, 403



@bp.get('/users')
@login_required
@check_roles(['attend'])
def users():
    user = User.objects.filter(cpfcnpj=request.args.get('id')).only('name', 'email').first()
    if user:
        return {'result': {'name': user.name, 'email': user.email}}
    else:
        return {'error': 'Usuário não encontrado'}


@bp.get('/blacklist')
@login_required
@check_roles(['settings'])
def get_blacklist():
    return {'result': Blacklist.objects().only('id', 'name', 'start', 'end') }

@bp.post('/blacklist')
@login_required
@check_roles(['settings'])
@get_json
def post_blacklist(data):
    name = data.get('name')
    start = data.get('start')
    end = data.get('end')
    if not (name and start and end):
        abort(400)
    try:
        fromdate = datetime.strptime(f'{start} 00', '%Y-%m-%d %H').timestamp()
        enddate = datetime.strptime(f'{end} 23:59:59', '%Y-%m-%d %H:%M:%S').timestamp()
    except Exception:
        return {'error': 'Data inválida'}, 400

    bookings = Booking.objects.filter(Q(start__gte=fromdate) & Q(start__lte=enddate)).order_by('start')
    if bookings:
        if data.get('force'):
            for b in bookings:
                b.send_mail(delete=True, reason=name)
        else:
            return {'result': len(bookings)}

    blacklist = Blacklist(
        name = name,
        user = current_user,
        start = fromdate,
        end = enddate,
    )
    blacklist.save()
    return {'result': '0'}

@bp.delete('/blacklist')
@login_required
@check_roles(['settings'])
@get_json
def delete_blacklist(data):
    id = data.get('delete')
    if not id or len(id) < 12:
        abort(400)
    b = Blacklist.objects.get_or_404(id=id)
    try:
        b.delete()
        return {'result': 'deleted'}
    except Exception as e:
        notify(_('Error saving to database'), e)
        return {'error': _('Error saving to database')}, 400


# svcs = {services[t]['name']: c for t, c in Counter(k for k in booking.services).most_common()}
