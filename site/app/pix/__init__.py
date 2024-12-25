from flask import Blueprint, current_app
bp = Blueprint('pix', __name__)

from .. import db
class Pix(db.DynamicDocument):
    pass

from . import routes

