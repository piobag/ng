from bson import ObjectId

from flask import Blueprint, abort
from apifairy import authenticate, body, response, other_responses

from api import db
from api.models import User, Message
from api.auth import token_auth
from api.decorators import paginated, get_json
from api.schemas import DateTimePaginationSchema

messages = Blueprint('messages', __name__)


@messages.route('/messages', methods=['POST'])
@authenticate(token_auth)
@get_json
def new(data):
    """Create a new post"""
    user = token_auth.current_user()
    message = Message(user=ObjectId(user['_id']), **data)
    new_msg = message.dict()
    del new_msg['id']
    new_msg['user'] = ObjectId(new_msg['user'])
    new_id = db.message.insert_one(new_msg)
    message.id = new_id.inserted_id
    return message.format_result([message.dict()])[0]


@messages.route('/messages/<int:id>', methods=['GET'])
@authenticate(token_auth)
@other_responses({404: 'Message not found'})
def get(id):
    """Retrieve a post by id"""
    return db.session.get(Message, id) or abort(404)


@messages.route('/messages', methods=['GET'])
@authenticate(token_auth)
@paginated
def all(pg):
    """Retrieve all messages"""
    result = Message.get_all(pg)
    pagination = {
        'count': len(result['data']),
        'limit': pg['limit'],
        'offset': pg['offset'],
        'total': result['total'],
    }
    return {'data': result['data'], 'pagination': pagination}

@messages.route('/users/<id>/messages', methods=['GET'])
@authenticate(token_auth)
@paginated
@other_responses({404: 'User not found'})
def user_all(pg, id):
    """Retrieve all messages from a user"""
    result = Message.get_feed([ObjectId(id)], pg)
    pagination = {
        'count': len(result['data']),
        'limit': pg['limit'],
        'offset': pg['offset'],
        'total': result['total'],
    }
    return {'data': result['data'], 'pagination': pagination}

@messages.route('/messages/<int:id>', methods=['PUT'])
@authenticate(token_auth)
@other_responses({403: 'Not allowed to edit this post',
                  404: 'Message not found'})
def put(data, id):
    """Edit a post"""
    post = db.session.get(Message, id) or abort(404)
    if post.author != token_auth.current_user():
        abort(403)
    post.update(data)
    db.session.commit()
    return post

@messages.route('/messages/<int:id>', methods=['DELETE'])
@authenticate(token_auth)
@other_responses({403: 'Not allowed to delete the post'})
def delete(id):
    """Delete a post"""
    post = db.session.get(Message, id) or abort(404)
    if post.author != token_auth.current_user():
        abort(403)
    db.session.delete(post)
    db.session.commit()
    return '', 204

@messages.route('/feed', methods=['GET'])
@authenticate(token_auth)
@paginated
def feed(pg):
    """Retrieve the user's post feed"""
    user = token_auth.current_user()
    follows = db.follows.find({'follower': ObjectId(user['_id'])}, {'_id': 0, 'followed': 1})
    flist = [f.get('followed') for f in follows]
    flist.append(ObjectId(user['_id']))
    result = Message.get_feed(flist, pg)    
    pagination = {
        'count': len(result['data']),
        'limit': pg['limit'],
        'offset': pg['offset'],
        'total': result['total'],
    }
    return {'data': result['data'], 'pagination': pagination}
