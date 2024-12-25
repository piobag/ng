import re
from datetime import datetime, timezone
from bson import ObjectId

from apifairy.decorators import other_responses
from flask import Blueprint, abort
from apifairy import authenticate, body, response

from api import db
from api.models import User
# from api.schemas import UserSchema, UpdateUserSchema, EmptySchema
from api.auth import token_auth
from api.decorators import paginated, get_json
from .cpfcnpj import verify_cpfcnpj


users = Blueprint('users', __name__)
# user_schema = UserSchema()
# users_schema = UserSchema(many=True)
# update_user_schema = UpdateUserSchema(partial=True)

@users.route('/users', methods=['POST'])
@get_json
# @body(user_schema)
# @response(user_schema, 201)
def new(data):
    """Register a new user"""
    # Validação dos campos
    username = data.get('username')
    if not username:
        return {'errors': {'username': 'Preencha seu nome completo'}}, 400
    username = username.strip()
    if len(username) < 3 or len(username) > 128:
        return {'errors': {'username': 'Tamanho do nome inválido'}}, 400
    cpfcnpj = data.get('cpfcnpj')
    if not cpfcnpj:
        return {'errors': {'cpfcnpj': 'Preencha seu CPF.'}}, 400
    if not verify_cpfcnpj(cpfcnpj):
        return {'errors': {'cpfcnpj': 'CPF inválido.'}}, 400
    cpfcnpj = re.sub('\D', '', cpfcnpj)
    email = data.get('email')
    if not email:
        return {'errors': {'email': 'Preencha seu email'}}, 400
    email = email.strip().lower()
    if not re.fullmatch(
            '^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*@(?:\w+\.)+[A-Za-z0-9]+$',
            email):
        return {'errors': {'email': 'Endereço de email inválido'}}, 400
    password = data.get('password')
    if not password:
        return {'errors': {'password': 'Preencha sua senha'}}, 400
    # Validação no banco
    if db.user.find_one({'email': email}, {'_id': 1}):
        return {'errors': {'email': 'Email já cadastrado'}}, 400

    if db.user.find_one({'cpfcnpj': cpfcnpj}, {'_id': 1}):
        return {'errors': {'cpfcnpj': 'CPF já cadastrado no sistema.'}}, 400

    user = User(name=username, email=email, cpfcnpj=cpfcnpj)
    user.set_password(data['password'])
    new_user = {
        'name': user.name,
        'email': user.email,
        'password': user.password,
        'cpfcnpj': user.cpfcnpj,
        'confirmed_at': datetime.now(timezone.utc).timestamp(),
        'last_seen': datetime.now(timezone.utc).timestamp(),
    }
    uid = db.user.insert_one(new_user)
    return {'id': str(uid.inserted_id) }, 201


@users.route('/users', methods=['GET'])
@authenticate(token_auth)
# @paginated_response(users_schema)
def all():
    """Retrieve all users"""
    return User.select()


@users.route('/users/<int:id>', methods=['GET'])
@authenticate(token_auth)
# @response(user_schema)
@other_responses({404: 'User not found'})
def get(id):
    """Retrieve a user by id"""
    return db.session.get(User, id) or abort(404)


@users.route('/users/<userid>', methods=['GET'])
@authenticate(token_auth)
# @response(user_schema)
@other_responses({404: 'User not found'})
def get_by_userid(userid):
    """Retrieve a user by user id"""
    if not (userid and len(userid) == 24):
        abort(400)
    user = db.user.find_one({'_id': ObjectId(userid)})
    if not user:
        abort(404)
    u = User(**user)
    return u.to_dict()

@users.route('/me', methods=['GET'])
@token_auth.login_required
# @response(user_schema)
def me():
    """Retrieve the authenticated user"""
    return token_auth.current_user()


@users.route('/me', methods=['PUT'])
@token_auth.login_required
@get_json
def put(args):
    """Edit user information"""
    user = token_auth.current_user()
    u = User(**user)
    db_set = {}
    # Password
    if 'password' in args:
        if ('old_password' not in args or
                               not u.verify_password(args['old_password'])):
            return {'errors': {'old_password': 'Senha inválida'}}, 400
        pwd = args['password'].strip()
        if len(pwd) < 3:
            return {'errors': {'password': 'A senha precisa ter mais de 3 caracteres'}}, 400
        u.set_password(pwd)
        db_set['password'] = u.password
    # Profile
    name = args.get('name')
    if name and name.strip() != user['name']:
        db_set['name'] = name.strip()
    if 'tel' in args:
        tel = re.sub('\D', '', args.get('tel'))
        if tel and tel != user['tel']:
            db_set['tel'] = tel
    if 'cpfcnpj' in args:
        cpfcnpj = re.sub('\D', '', args.get('cpfcnpj'))
        if cpfcnpj and not user['cpfcnpj']:
            db_set['cpfcnpj'] = cpfcnpj
    # Save db
    if db_set:
        db.user.update_one({'_id': ObjectId(user['_id'])}, {'$set': db_set})
        for attr, value in db_set.items():
            user[attr] = value

    return user


@users.route('/me/following', methods=['GET'])
@authenticate(token_auth)
# @paginated_response(users_schema, order_by=User.username)
def my_following():
    """Retrieve the users the logged in user is following"""
    user = token_auth.current_user()
    return user.following.select()


@users.route('/me/followers', methods=['GET'])
@authenticate(token_auth)
# @paginated_response(users_schema, order_by=User.username)
def my_followers():
    """Retrieve the followers of the logged in user"""
    user = token_auth.current_user()
    return user.followers.select()


@users.route('/me/following/<id>', methods=['GET'])
@authenticate(token_auth)
@other_responses({404: 'User is not followed'})
def is_followed(id):
    """Check if a user is followed"""
    user = token_auth.current_user()
    followed_user = db.user.find_one({'_id': ObjectId(id)}, {'_id': 1}) or abort(400)
    u = User(**user)
    u.id = ObjectId(user['_id'])
    if not u.is_following(followed_user.get('_id')):
        abort(404)
    return {}, 204


@users.route('/me/following/<id>', methods=['POST'])
@authenticate(token_auth)
@other_responses({404: 'User not found', 409: 'User already followed.'})
def follow(id):
    """Follow a user"""
    user = token_auth.current_user()
    followed_user = db.user.find_one({'_id': ObjectId(id)}, {'_id': 1}) or abort(404)
    u = User(**user)
    u.id = ObjectId(user['_id'])
    if u.is_following(followed_user.get('_id')):
        abort(409)
    u.follow(followed_user.get('_id'))
    return {}, 204


@users.route('/me/following/<id>', methods=['DELETE'])
@authenticate(token_auth)
@other_responses({404: 'User not found', 409: 'User is not followed.'})
def unfollow(id):
    """Unfollow a user"""
    user = token_auth.current_user()
    unfollowed_user = db.user.find_one({'_id': ObjectId(id)}, {'_id': 1}) or abort(404)
    u = User(**user)
    u.id = ObjectId(user['_id'])
    if not u.is_following(unfollowed_user.get('_id')):
        abort(409)
    u.unfollow(unfollowed_user.get('_id'))
    return {}, 204


@users.route('/users/<int:id>/following', methods=['GET'])
@authenticate(token_auth)
# @paginated_response(users_schema, order_by=User.username)
@other_responses({404: 'User not found'})
def following(id):
    """Retrieve the users this user is following"""
    user = db.session.get(User, id) or abort(404)
    return user.following.select()


@users.route('/users/<int:id>/followers', methods=['GET'])
@authenticate(token_auth)
# @paginated_response(users_schema, order_by=User.username)
@other_responses({404: 'User not found'})
def followers(id):
    """Retrieve the followers of the user"""
    user = db.session.get(User, id) or abort(404)
    return user.followers.select()
