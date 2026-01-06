from flask import Blueprint, request, jsonify, send_file, session
import time
import re
from utils.captcha import generate_captcha_text, generate_captcha_image
from services.user_service import register_service, login_service

auth_bp = Blueprint('auth', __name__)
CAPTCHA_EXPIRE = 300  # 5分钟

@auth_bp.route('/captcha')
def get_captcha():
    text = generate_captcha_text()
    session['captcha'] = {'text': text, 'expires_at': time.time() + CAPTCHA_EXPIRE}
    img_io = generate_captcha_image(text)
    return send_file(img_io, mimetype='image/png')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    account = data.get('account', '').strip()      # 前端传的是 account（原 email）
    nickname = data.get('username', '').strip()
    password = data.get('password', '')
    captcha_input = data.get('captcha', '').strip()

    # 必填校验
    if not account or not nickname or not password or not captcha_input:
        return jsonify({'error': '账号、昵称、密码和验证码不能为空'}), 400

    # 账号格式校验：字母、数字、下划线、@、点，3-20位
    if not re.match(r"^[a-zA-Z0-9_@.]{3,20}$", account):
        return jsonify({'error': '账号只能包含字母、数字、下划线、@、点，长度3-20位'}), 400

    # 昵称长度校验
    if len(nickname) < 2 or len(nickname) > 20:
        return jsonify({'error': '昵称长度需为2-20个字符'}), 400

    if len(password) < 6:
        return jsonify({'error': '密码至少6位'}), 400

    # 验证码校验
    captcha_data = session.get('captcha')
    now = time.time()
    if not captcha_data or now > captcha_data['expires_at']:
        return jsonify({'error': '验证码已过期或未获取'}), 400
    if captcha_data['text'].lower() != captcha_input.lower():
        return jsonify({'error': '验证码错误'}), 400

    session.pop('captcha', None)

    # 调用注册服务（传 account 到 email 字段）
    user, err = register_service(email=account, username=nickname, password=password)
    if err:
        return jsonify({'error': err}), 400

    return jsonify({'message': '注册成功！', 'user': user}), 201

@auth_bp.route('/login', methods=['POST'])
def login():

    data = request.get_json()
    account = data.get('email')      # 登录用 account（存于 email 字段）
    password = data.get('password')
    user, err = login_service(email=account, password=password)
    if err:
        return jsonify({'error': err}), 401
    return jsonify(user), 200