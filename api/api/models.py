import uuid
from bson import ObjectId
from bson.json_util import dumps, loads
from typing import List, Optional, Any

from pydantic_core import core_schema
from pydantic import BaseModel, Field


from datetime import datetime, timedelta, timezone
from hashlib import md5
import secrets
from time import time
from typing import Optional

from flask import current_app, url_for
import jwt
import sqlalchemy as sa
from sqlalchemy import orm as so
from werkzeug.security import generate_password_hash, check_password_hash

from . import db

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(
            cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, value) -> ObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")

        return ObjectId(value)

class Updateable:
    def update(self, data):
        for attr, value in data.items():
            setattr(self, attr, value)

class Follows(BaseModel):
    follower: PyObjectId
    followed: PyObjectId

class Token(BaseModel):
    id: PyObjectId = Field(default_factory=uuid.uuid4, alias="_id")
    access_token: Optional[str] = None
    access_expiration: Optional[float] = None
    refresh_token: Optional[str] = None
    refresh_expiration: Optional[float] = None
    user: PyObjectId

    @property
    def access_token_jwt(self):
        return jwt.encode({'token': self.access_token},
                          current_app.config['SECRET_KEY'],
                          algorithm='HS256')

    def generate(self):
        self.access_token = secrets.token_urlsafe()
        self.access_expiration = (datetime.now(timezone.utc) + \
            timedelta(minutes=current_app.config['ACCESS_TOKEN_MINUTES'])).timestamp()
        self.refresh_token = secrets.token_urlsafe()
        self.refresh_expiration = (datetime.now(timezone.utc) + \
            timedelta(days=current_app.config['REFRESH_TOKEN_DAYS'])).timestamp()

    def expire(self, delay=None):
        if delay is None:  # pragma: no branch
            # 5 second delay to allow simultaneous requests
            delay = 5 if not current_app.testing else 0
        db.token.update_one({'_id': self.id}, {'$set': {
            'access_expiration': (datetime.now(timezone.utc) + timedelta(seconds=delay)).timestamp(),
            'refresh_expiration': (datetime.now(timezone.utc) + timedelta(seconds=delay)).timestamp()
        }})

    @staticmethod
    def clean():
        """Remove any tokens that have been expired for more than a day."""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).timestamp()
        db.token.delete_many({'refresh_expiration': {'$lt': yesterday}})

    @staticmethod
    def from_jwt(access_token_jwt):
        access_token = None
        try:
            access_token = jwt.decode(access_token_jwt,
                                      current_app.config['SECRET_KEY'],
                                      algorithms=['HS256'])['token']
            tk = db.token.find_one({'access_token': access_token})
            if tk:
                token = Token(**tk)
                return token
        except jwt.PyJWTError:
            pass

class User(Updateable, BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=uuid.uuid4, alias="_id")
    name: str
    email: str
    cpfcnpj: Optional[str] = None
    password: Optional[str] = None

    tel: Optional[str] = None
    confirmed_at: Optional[float] = None
    last_seen: Optional[float] = Field(default_factory=datetime.now(timezone.utc).timestamp)

    @property
    def avatar(self):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon'

    def ping(self):
        self.last_seen = datetime.now(timezone.utc).timestamp()

    def to_dict(self):
        return {
            '_id': str(self.id),
            'name': self.name,
            'cpfcnpj': self.cpfcnpj,
            'email': self.email,
            'password': self.password,
            'tel': self.tel,
            'avatar_url': self.avatar,
            'confirmed_at': self.confirmed_at if self.confirmed_at else None,
            'last_seen': self.last_seen,
        }

    def __repr__(self):  # pragma: no cover
        return '<User {}>'.format(self.name)

    def followers(self):
        follows = db.follows.find({'followed': str(self.id)}, {'_id': 0, 'follower': 1})
        return [follow['follower'] for follow in follows]

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def verify_password(self, password):
        if self.password:  # pragma: no branch
            return check_password_hash(self.password, password)

    def generate_auth_token(self):
        token = Token(user=self.id)
        token.generate()
        return token
    
    @staticmethod
    def verify_access_token(access_token_jwt, refresh_token=None):
        token = Token.from_jwt(access_token_jwt)
        if token:
            if token.access_expiration > datetime.now(timezone.utc).timestamp():
                db.user.update_one({'_id': token.user}, {'$set': {'last_seen': datetime.now(timezone.utc).timestamp()}})
                u = db.user.find_one({'_id': token.user})
                user = User(**u)
                # user = loads(dumps(u))
                # user['_id'] = str(user['_id'])
                return user.to_dict()

    @staticmethod
    def verify_refresh_token(refresh_token, access_token_jwt):
        token = Token.from_jwt(access_token_jwt)
        if token and token.refresh_token == refresh_token:
            if token.refresh_expiration > datetime.now(timezone.utc).timestamp():
                return token
            # someone tried to refresh with an expired token
            # revoke all tokens from this user as a precaution
            db.token.delete_many({'user': token.user})

    def generate_reset_token(self):
        return jwt.encode(
            {
                'exp': time() + current_app.config['RESET_TOKEN_MINUTES'] * 60,
                'reset_email': self.email,
            },
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_reset_token(reset_token):
        try:
            data = jwt.decode(reset_token, current_app.config['SECRET_KEY'],
                              algorithms=['HS256'])
        except jwt.PyJWTError:
            return
        return db.user.find_one({'email': data['reset_email']})

    def following(self):
        follows = db.follows.find({'follower': self.id}, {'_id': 0, 'followed': 1})
        return [follow['followed'] for follow in follows]

    def is_following(self, user):
        return user in self.following()

    def follow(self, user):
        if not self.is_following(user):
            db.follows.insert_one({'follower': self.id, 'followed': user})
    def unfollow(self, user):
        if self.is_following(user):
            db.follows.delete_many({'follower': self.id, 'followed': user})

class Role(BaseModel):
    name: str
    text: str
    parent: Optional[PyObjectId] = None
    desc: Optional[str] = None

class RoleBind(BaseModel):
    user: PyObjectId
    role: PyObjectId

class Message(BaseModel):
    id: PyObjectId = Field(default_factory=uuid.uuid4, alias="_id")
    text: str
    timestamp: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    user: PyObjectId

    @property
    def url(self):
        return url_for('messages.get', id=self.id)
    
    @staticmethod
    def format_result(result):
        data = []
        for m in result:
            user = db.user.find_one({'_id': ObjectId(m.get('user'))})
            u = User(**user)
            data.append({
                'id': str(m.get('_id') or m.get('id')),
                'text': m.get('text'),
                'timestamp': m.get('timestamp'),
                'user': {
                    'id': str(u.id),
                    'name': u.name,
                    'avatar_url': u.avatar,
                }
            })
        return data

    def get_feed(following, pg):
        total = db.message.count_documents({'user': {'$in': following}})
        result = db.message.find({'user': {'$in': following}}).sort('timestamp', -1).skip(pg['offset']).limit(pg['limit'])
        return {'total': total, 'data': Message.format_result(result)}

    def get_all(pg):
        total = db.message.count_documents({})
        result = db.message.find({}).sort('timestamp', -1).skip(pg['offset']).limit(pg['limit'])
        return {'total': total, 'data': Message.format_result(result)}

