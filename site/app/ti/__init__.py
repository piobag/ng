from flask import Blueprint
from .. import db

bp = Blueprint('ti', __name__)

from . import routes
