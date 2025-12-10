"""
帖子 API 蓝图：处理 HTTP 请求/响应，调用服务层完成业务
支持：
- POST /api/posts：创建帖子（需登录）
- GET /api/posts：获取所有帖子（公开）
- GET /api/posts/<id>：获取帖子详情（含评论，公开）
"""
from database import db
from flask import Blueprint, request, jsonify
from utils.auth_utils import login_required
from services.post_service import (
    create_post,
    get_all_posts,
    get_post_with_paginated_comments,
    get_posts_paginated_by_sort,
    get_random_posts
)
from utils.response_utils import success, error


post_bp = Blueprint('posts', __name__)


# 支持两种路径：/api/posts 和 /api/posts/
@post_bp.route('', methods=['POST'])
@post_bp.route('/', methods=['POST'])
@login_required
def create_post_route(current_user):
    """发布新脑洞（需登录）"""
    data = request.get_json()
    if not data:
        return error("Request body must be valid JSON.", 400)

    title = data.get('title')
    content = data.get('content')
    tags = data.get('tags', [])

    try:
        post = create_post(current_user.id, title, content, tags)
        return success(post.to_dict(), "Post created successfully.")
    except ValueError as e:
        return error(str(e), 400)
    except Exception as e:
        db.session.rollback()
        print("Full error:", repr(e))
        import traceback
        traceback.print_exc()
        return error("Failed to create post.", 500)


@post_bp.route('', methods=['GET'])
@post_bp.route('/', methods=['GET'])
def get_posts():
    """获取分页帖子（支持多种排序）"""
    try:
        sort = request.args.get('sort', 'newest')  # 新增参数
        limit = request.args.get('limit', default=10, type=int)
        before = request.args.get('before', default=None, type=str)
        after = request.args.get('after', default=None, type=str)

        # 安全限制
        limit = min(limit, 50)

        # 调用新服务函数
        posts, has_more = get_posts_paginated_by_sort(
            sort_type=sort,
            limit=limit,
            before=before,
            after=after
        )

        return success({
            "posts": [post.to_dict() for post in posts],
            "has_more": has_more
        }, "Posts retrieved successfully.")

    except ValueError as e:
        return error(str(e), 400)
    except Exception as e:
        print("Get Posts Error:", repr(e))
        return error("Failed to retrieve posts.", 500)


@post_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        comment_sort = request.args.get('comment_sort', 'hot') 
        if comment_sort not in ('hot', 'time_desc'):
            return jsonify({'error': 'Invalid comment_sort. Use: hot, time_desc'}), 400

        limit = min(max(request.args.get('limit', 10, type=int), 1), 50) #数量限制
        before = request.args.get('before', None, type=str)
        after = request.args.get('after', None, type=str)

        post, comments, has_more = get_post_with_paginated_comments(
            post_id=post_id,
            limit=limit,
            before=before,
            after=after,
            sort=comment_sort  # 传入排序方式
        )
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        return jsonify({
            'post': post.to_dict(),
            'comments': comments,
            'has_more': has_more
        }), 200
    except Exception as e:
        print("Get Post Error:", repr(e))
        return jsonify({'error': 'Failed to load post'}), 500
    

@post_bp.route('/roam', methods=['GET'])
def get_roam_posts():
    """漫游页：随机获取帖子"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        limit = min(max(limit, 1), 50)  # 限制 1~50

        posts = get_random_posts(limit=limit)

        return success({
            "posts": [post.to_dict() for post in posts]
        }, "Random posts retrieved.")

    except Exception as e:
        print("Roam Posts Error:", repr(e))
        return error("Failed to fetch roam posts.", 500)