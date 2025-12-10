# backend/api/interaction_bp.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.interaction_service import (
    toggle_like,
    toggle_question,
    get_interaction_status
)
#from utils.decorators import validate_json
from models import User

interaction_bp = Blueprint('interaction', __name__)


def _get_user_id():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        raise Exception("User not found")
    return user.id


@interaction_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@jwt_required()
def like_post(post_id):
    user_id = _get_user_id()
    success, new_state, count = toggle_like(user_id, 'post', post_id)
    if not success:
        return jsonify({'error': 'Failed to toggle like'}), 500
    return jsonify({
        'action': 'like',
        'active': new_state,
        'count': count
    })


@interaction_bp.route('/posts/<int:post_id>/question', methods=['POST'])
@jwt_required()
def question_post(post_id):
    user_id = _get_user_id()
    success, new_state, count = toggle_question(user_id, 'post', post_id)
    if not success:
        return jsonify({'error': 'Failed to toggle question'}), 500
    return jsonify({
        'action': 'question',
        'active': new_state,
        'count': count
    })


@interaction_bp.route('/comments/<int:comment_id>/like', methods=['POST'])
@jwt_required()
def like_comment(comment_id):
    user_id = _get_user_id()
    success, new_state, count = toggle_like(user_id, 'comment', comment_id)
    if not success:
        return jsonify({'error': 'Failed to toggle like'}), 500
    return jsonify({
        'action': 'like',
        'active': new_state,
        'count': count
    })


@interaction_bp.route('/comments/<int:comment_id>/question', methods=['POST'])
@jwt_required()
def question_comment(comment_id):
    user_id = _get_user_id()
    success, new_state, count = toggle_question(user_id, 'comment', comment_id)
    if not success:
        return jsonify({'error': 'Failed to toggle question'}), 500
    return jsonify({
        'action': 'question',
        'active': new_state,
        'count': count
    })


@interaction_bp.route('/posts/<int:post_id>/status', methods=['GET'])
@jwt_required()
def get_post_interaction_status(post_id):
    user_id = _get_user_id()
    status = get_interaction_status(user_id, 'post', post_id)
    return jsonify(status)


@interaction_bp.route('/comments/<int:comment_id>/status', methods=['GET'])
@jwt_required()
def get_comment_interaction_status(comment_id):
    user_id = _get_user_id()
    status = get_interaction_status(user_id, 'comment', comment_id)
    return jsonify(status)