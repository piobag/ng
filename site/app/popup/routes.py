from os import path

from flask import request, current_app, abort, send_file
from flask_login import login_required
from flask_babel import _
from werkzeug.utils import secure_filename
from mongoengine.errors import ValidationError

from . import bp, Popup
from ..auth import check_roles, get_json, notify


@bp.get('/')
@login_required
@check_roles(['settings'])
def index():
    return { 'result': [{
                'id': str(x.id),
                'name': x.name,
                'route': current_app.config['POPUP_ROUTES'][x.route],
                'active': x.active,
                'file': str(x.file.grid_id)
            } for x in Popup.objects()] }

@bp.post('/')
@login_required
@check_roles(['settings'])
def new():
    if not request.form.get('desc') or \
            not request.form.get('page') in current_app.config['POPUP_ROUTES']:
        return {'error': 'Preencha todos os campos'}, 400
    if request.files['file_input'].filename == '':
        return {'error': 'Nenhum arquivo recebido'}, 400
    filename = secure_filename(request.files['file_input'].filename)
    if not path.splitext(filename)[1].lower() in ['.jpg', '.jpeg', '.png', '.gif']:
        return {'error': 'Tipo de arquivo inválido'}, 400
    popup = Popup(
        name = request.form['desc'],
        route = request.form['page'],
        active = True if request.form['active'] == 'true' else False,
    )
    popup.file.put(request.files['file_input'].stream, content_type=request.files['file_input'].content_type)
    try:
        popup.save()
        return {'result': str(popup.id)}
    except Exception as e:
        notify(_('Error saving to database'), e)
        return {'error': _('Error saving to database')}, 400

@bp.put('/')
@login_required
@check_roles(['settings'])
@get_json
def edit(data):
    if data.get('enable'):
        p = Popup.objects.get_or_404(id=data['enable'])
        p.active = True
        p.save()
        return {'result': 'enabled'}
    elif data.get('disable'):
        p = Popup.objects.get_or_404(id=data['disable'])
        p.active = False
        p.save()
        return {'result': 'disabled'}
    abort(400)

@bp.delete('/')
@login_required
@check_roles(['settings'])
@get_json
def delete(data):
    oid = data.get('delete')
    if not oid or len(oid) < 12:
        abort(400)
    p = Popup.objects.get_or_404(id=oid)
    try:
        p.delete()
        return {'result': 'deleted'}
    except Exception as e:
        notify(_('Error saving to database'), e)
        return {'error': _('Error saving to database')}, 400
    
@bp.get('/view')
def view():
    oid = request.args.get('id')
    if not oid or len(oid) < 12:
        abort(400)
    try:
        p = Popup.objects.get_or_404(id=oid)
    except ValidationError:
        abort(400)
    return send_file(
        p.file.get(),
        mimetype=p.file.content_type,
    )
