# backend/api/auth_bp.py
from flask import Blueprint, request, jsonify
from services.user_service import login_service, register_service
from utils.response_utils import success, error
from utils.auth_utils import authenticate_user, encode_auth_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not all([email, username, password]):
        return error("Missing required fields.", 400)

    user, err = register_service(email, username, password)
    if err:
        return error(err, 400)
    return success(user, "User registered successfully.")

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = authenticate_user(email, password)
    if user:
        token = encode_auth_token(user.id)  # 生成 JWT
        return jsonify({
            'message': '登录成功',
            'token': token
        }), 200
    else:
        return jsonify({'error': '邮箱或密码错误'}), 401