from bson.objectid import ObjectId

from flask import (
    request,
    abort,
    send_file,
)
from flask_login import current_user

from . import bp
from .. import db
from ..finance import Devol
from ..auth import get_roles


@bp.route('/', methods=['GET'])
@get_roles
def fs(roles):
    digitizer = request.args.get('digitizer')
    if digitizer:
        if not (current_user.is_authenticated and ('digitizer' in roles or 'digitizer-signer' in roles)):
            abort(403)
        try:
            gridfs = db.ImageGridFsProxy(collection_name='images')
            image = gridfs.fs.find_one({'_id': ObjectId(digitizer), 'app': 'digitizer'})
            if image:
                return send_file(
                    image,
                    mimetype=image.content_type
                )
            else:
                abort(404)
        except:
            abort(400)
    transf = request.args.get('transf')
    if transf:
        try:
            devol = Devol.objects.get_or_404(id=transf)
            return send_file(
                devol.transf.get(),
                mimetype=devol.transf.content_type
            )
        except:
            abort(404)
    # test = request.args.get('test')
    # if test:
    #     try:
    #         gridfs = db.ImageGridFsProxy(collection_name='images')
    #         file = gridfs.fs.find_one({'_id': ObjectId(test)})
    #         if file:
    #             return send_file(
    #                 file,
    #                 mimetype=file.content_type
    #             )
    #     except:
    #         abort(404)
    abort(400)
