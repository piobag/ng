import pytz
from os import getenv, path
from datetime import datetime
from importlib import import_module

from flask import request, abort, send_file
from flask_login import login_required
from flask_babel import _
from werkzeug.utils import secure_filename

from . import bp, DevReport
from ..auth import check_roles, get_json, notify
from ..base import User

@bp.get('/dev')
@login_required
@check_roles(['audit', 'adm'])
def get_dev():
    page = request.args.get('page', 1, type=int)
    reports = DevReport.objects().only('id', 'date', 'hours').order_by('-date').paginate(page=page, per_page=5)
    
    all = DevReport.objects()
    total = 0
    for i in all:
        total += i.hours
    balance = total - (160 * len(all))
    return {
        'result': [x.to_dict() for x in reports.items],
        'balance': balance,
    }

@bp.post('/dev')
@login_required
@check_roles(['adm'])
def new_dev():
    if request.files['devreport_file'].filename == '':
        return {'error': 'Nenhum arquivo encontrado'}
    filename = secure_filename(request.files['devreport_file'].filename)
    if not path.splitext(filename)[1].lower() in ['.pdf', '.doc', '.docx']:
        return {'error': 'Extensão do arquivo inválida'}
    dev = DevReport(
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').astimezone(pytz.utc).timestamp(),
        hours = request.form['hours'],
    )
    dev.doc.put(request.files['devreport_file'].stream, content_type=request.files['devreport_file'].content_type)
    try:
        dev.save()
        return {'result': str(dev.id)}
    except Exception as e:
        msg = _('Error saving to database')
        notify(msg, e)
        return {'error': msg}, 400


@bp.get('/dev/doc')
@login_required
@check_roles(['audit', 'adm'])
def get_dev_doc():
    if request.args.get('id'):
        devreport = DevReport.objects.get_or_404(id=request.args['id'])
        return send_file(
            devreport.doc.get(),
            mimetype=devreport.doc.content_type,
        )
    abort(404)