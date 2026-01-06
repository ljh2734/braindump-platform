import jwt
from datetime import datetime, timedelta, timezone
from flask import current_app, request
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from database import db
from utils.response_utils import error

def encode_auth_token(user_id):
    """生成 JWT Token"""
    try:
        now = datetime.now(timezone.utc)
        payload = {
            'exp': int((now + timedelta(days=7)).timestamp()),
            'iat': int(now.timestamp()),
            'sub': str(user_id)  # 转为字符串
        }
        return jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )
    except Exception as e:
        return str(e)

def decode_auth_token(auth_token):
    """解码 JWT Token，返回 user_id 或错误信息"""
    try:
        payload = jwt.decode(
            auth_token,
            current_app.config.get('SECRET_KEY'),
            algorithms=['HS256']
        )
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Token expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

def authenticate_user(email, password):
    """验证用户凭据"""
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        return user
    return None

def register_user(email, username, password):
    """注册新用户（带唯一性校验）"""
    # 检查用户名是否已存在
    if User.query.filter_by(email=email).first():
        raise ValueError('Email already registered.')
    if User.query.filter_by(username=username).first():
        raise ValueError('Username already taken.')
    
    user = User(email=email, username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user

def current_user():
    """
    从请求头 Authorization: Bearer <token> 中解析当前用户。
    成功返回 User 对象，失败返回 None。
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(" ")[1]
    result = decode_auth_token(token)

    # 如果 result 是字符串，说明是错误信息
    if isinstance(result, str):
        return None

    try:
        user_id = int(result)
    except (ValueError, TypeError):
        return None

    user = User.query.get(user_id)
    return user


from functools import wraps
from flask import request, jsonify

def login_required(f):
    """
    装饰器：验证 JWT Token，注入 current_user
    使用后，视图函数第一个参数为 user 对象
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return error("Token is missing or invalid format.", 401)

        token = auth_header.split(" ")[1]
        result = decode_auth_token(token)

        try:
            user_id = int(result)
        except (ValueError, TypeError):
            return error(result, 401)

        from models import User
        user = User.query.get(user_id)
        if not user:
            return error("User not found.", 401)

        return f(user, *args, **kwargs)
    return decorated_function