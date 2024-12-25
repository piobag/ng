from flask import Blueprint

from .. import db

bp = Blueprint('fs', __name__)

from . import routes