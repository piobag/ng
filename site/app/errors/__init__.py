from flask import Blueprint, render_template, request
from flask_babel import _

bp = Blueprint('errors', __name__)

def wants_json_response():
    return request.accept_mimetypes['application/json'] >= \
                                        request.accept_mimetypes['text/html']

@bp.app_errorhandler(400)
def bad_request_error(error):
    if wants_json_response():
        return {'error': _('Bad request')}, 400
    return render_template('landingpage.html', message=f"{_('Error')} 400: {_('Bad request')}!"), 400

@bp.app_errorhandler(403)
def forbidden_error(error):
    if wants_json_response():
        return {'error': _('Not permited')}, 403
    return render_template('landingpage.html', message=f"{_('Error')} 403: {_('Not permited')}!"), 403

@bp.app_errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return {'error': _('Not found')}, 404
    return render_template('landingpage.html', message=f"{_('Error')} 404: {_('Not found')}!"), 404


@bp.app_errorhandler(405)
def not_found_zero_error(error):
    return '', 404

@bp.app_errorhandler(500)
def internal_error(error):
    if wants_json_response():
        pass
#        return api_error_response(500)
    return render_template('error/500.html'), 500
