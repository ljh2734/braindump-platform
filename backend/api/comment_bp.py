"""评论 API 蓝图：仅处理 HTTP 请求/响应，调用服务层"""

from flask import Blueprint, request, jsonify
from utils.auth_utils import login_required
from services.comment_service import (
    create_comment,
    delete_comment,
    get_comment_tree,
    get_top_level_comment_replies_service
)


comment_bp = Blueprint('comment', __name__)


@comment_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@login_required
def create_comment_route(current_user, post_id):
    data = request.get_json()
    content = data.get('content', '')
    parent_id = data.get('parent_id')
    comment, error = create_comment(
        post_id=post_id,
        user_id=current_user.id,
        content=content,
        parent_id=parent_id
    )
    if error:
        code = 400 if 'required' in error or 'Parent' in error else 500
        return jsonify({'error': error}), code
    return jsonify({
        'id': comment.id,
        'content': comment.content,
        'user_id': comment.user_id,
        'post_id': comment.post_id,
        'parent_id': comment.parent_id,
        'like_count': 0,
        'question_count': 0,
        'created_at': comment.created_at.isoformat(),
        'author': comment.author.to_public_dict()
    }), 201


@comment_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment_route(current_user, comment_id):
    success, message = delete_comment(
        comment_id=comment_id,
        user_id=current_user.id,
        is_admin=current_user.is_admin
    )
    if not success:
        if "Permission denied" in message:
            return jsonify({'error': message}), 403
        elif "not found" in message.lower():
            return jsonify({'error': message}), 404
        else:
            return jsonify({'error': message}), 500
    return jsonify({'message': message}), 200


@comment_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments_route(post_id):
    try:
        tree = get_comment_tree(post_id)
        return jsonify(tree), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch comments'}), 500



@comment_bp.route('/top-level/<int:comment_id>/replies', methods=['GET'])
def get_top_level_comment_replies(comment_id):
    try:
        limit = min(max(request.args.get('limit', 10, type=int), 1), 50)
        after = request.args.get('after', None, type=str)
        replies, has_more, error = get_top_level_comment_replies_service(
            comment_id=comment_id,
            limit=limit,
            after=after
            # sort 固定为 time_asc，不再传入
        )
        if error:
            return jsonify({'error': error}), 404

        return jsonify({'replies': replies, 'has_more': has_more}), 200
    except Exception as e:
        print("Get Top-Level Replies Error:", repr(e))
        return jsonify({'error': 'Failed to load replies'}), 500