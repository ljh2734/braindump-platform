from flask import Blueprint, request, jsonify
from utils.auth_utils import login_required
from services.block_service import toggle_block, get_blocked_user_ids

block_bp = Blueprint('block', __name__)

@block_bp.route('/toggle', methods=['POST'])
@login_required
def toggle_block_route(current_user):
    data = request.get_json()
    blocked_id = data.get('user_id')
    
    if not isinstance(blocked_id, int):
        return jsonify({'error': 'user_id 必须是整数'}), 400
    
    try:
        is_now_blocked = toggle_block(current_user.id, blocked_id)
        return jsonify({'blocked': is_now_blocked}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@block_bp.route('/list', methods=['GET'])
@login_required
def list_blocks(current_user):
    blocked_ids = get_blocked_user_ids(current_user.id)
    return jsonify({'blocked_user_ids': blocked_ids}), 200

@block_bp.route('/check/<int:user_id>', methods=['GET'])
@login_required
def check_block_status(current_user, user_id):
    from services.block_service import is_blocked
    blocked_by_me = is_blocked(current_user.id, user_id)
    blocked_me = is_blocked(user_id, current_user.id)
    return jsonify({
        'blocked_by_me': blocked_by_me,
        'blocked_me': blocked_me
    }), 200