# backend/api/auth_bp.py
from flask import Blueprint, request, jsonify
from services.user_service import login_service, register_service
from utils.response_utils import success, error

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

    if not email or not password:
        return error("Email and password are required.", 400)

    result, err = login_service(email, password)
    if err:
        return error(err, 401)
    return success(result, "Login successful.")