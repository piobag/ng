from functools import wraps

from flask import Flask, request, abort

from .config import Config

# Mail
from flask_mail import Mail
mail = Mail()

from .whats import send_msg

app = Flask(__name__, template_folder='../templates')
app.config.from_object(Config)
# Mail
mail.init_app(app)

def get_json(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        data = request.get_json()
        if data and request.content_type == 'application/json':
            return f(data, *args, **kwargs)
        abort(400)
    return wrapped

@app.post("/send")
@get_json
def post_msg(data):
    return send_msg(data['msg'], data['tel'])

    # return "ok"