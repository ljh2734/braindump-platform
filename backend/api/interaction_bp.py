from flask import Blueprint, request, jsonify
from utils.auth_utils import login_required
from services.interaction_service import (
    toggle_like,
    toggle_question,
    get_interaction_status
)
from models import User

interaction_bp = Blueprint('interaction', __name__)

@interaction_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(current_user, post_id):
    success, new_state, count = toggle_like(current_user.id, 'post', post_id)
    if not success:
        return jsonify({'error': 'Failed to toggle like'}), 500
    return jsonify({
        'action': 'like',
        'active': new_state,
        'count': count
    })


@interaction_bp.route('/posts/<int:post_id>/question', methods=['POST'])
@login_required
def question_post(current_user, post_id):
    success, new_state, count = toggle_question(current_user.id, 'post', post_id)
    if not success:
        return jsonify({'error': 'Failed to toggle question'}), 500
    return jsonify({
        'action': 'question',
        'active': new_state,
        'count': count
    })


@interaction_bp.route('/comments/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(current_user, comment_id):
    success, new_state, count = toggle_like(current_user.id, 'comment', comment_id)
    if not success:
        return jsonify({'error': 'Failed to toggle like'}), 500
    return jsonify({
        'action': 'like',
        'active': new_state,
        'count': count
    })


@interaction_bp.route('/comments/<int:comment_id>/question', methods=['POST'])
@login_required
def question_comment(current_user, comment_id):
    success, new_state, count = toggle_question(current_user.id, 'comment', comment_id)
    if not success:
        return jsonify({'error': 'Failed to toggle question'}), 500
    return jsonify({
        'action': 'question',
        'active': new_state,
        'count': count
    })

# ===状态查询路由===
@interaction_bp.route('/posts/<int:post_id>/status', methods=['GET'])
@login_required
def get_post_interaction_status(current_user, post_id):
    status = get_interaction_status(current_user.id, 'post', post_id)
    return jsonify(status)


@interaction_bp.route('/comments/<int:comment_id>/status', methods=['GET'])
@login_required
def get_comment_interaction_status(current_user, comment_id):
    status = get_interaction_status(current_user.id, 'comment', comment_id)
    return jsonify(status)