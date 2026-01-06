from flask import Blueprint, request, jsonify
from utils.auth_utils import login_required
from services.message_service import send_message, get_conversation, get_contacts_with_last_message
from models import User

message_bp = Blueprint('message', __name__)

@message_bp.route('/contacts')
@login_required
def get_contacts(current_user):
    contacts = get_contacts_with_last_message(current_user.id)
    return jsonify({"contacts": contacts}), 200

@message_bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_messages(current_user, user_id):
    # 验证 user_id 是否有效
    if not User.query.get(user_id):
        return jsonify({'error': '用户不存在'}), 404
    messages = get_conversation(current_user.id, user_id)
    return jsonify({
        "messages": [msg.to_dict() for msg in messages]
    }), 200

@message_bp.route('/<int:user_id>', methods=['POST'])
@login_required
def create_message(current_user, user_id):
    data = request.get_json()
    content = data.get('content', '')
    try:
        msg = send_message(current_user.id, user_id, content)
        return jsonify(msg.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@message_bp.route('', methods=['POST'])
@login_required
def send_new_message(current_user):
    """发送私信"""
    data = request.get_json()
    content = data.get('content', '')
    receiver_id = data.get('receiver_id')
    
    if not isinstance(receiver_id, int):
        return jsonify({'error': 'receiver_id 必须是整数'}), 400
        
    try:
        msg = send_message(current_user.id, receiver_id, content)
        return jsonify(msg.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400