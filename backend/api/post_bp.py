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
    get_random_posts,
    search_posts_by_tags as get_search_posts_by_tags,
    _get_interaction_counts_for_posts
)
from utils.response_utils import success, error
import json
from models import Post, Tag
from datetime import datetime, timezone

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

@post_bp.route('/', methods=['GET'])
@post_bp.route('', methods=['GET'])
def get_posts():
    """获取所有帖子"""
    try:
        sort = request.args.get('sort', 'newest')
        limit = request.args.get('limit', default=10, type=int)
        before = request.args.get('before', default=None, type=str)
        after = request.args.get('after', default=None, type=str)

        limit = min(limit, 50)
        has_more = False

        #  现在 posts 已经是 List[dict]，无需再调用 .to_dict()
        posts, has_more = get_posts_paginated_by_sort(
            sort_type=sort,
            limit=limit,
            before=before,
            after=after
        )

        return success({
            "posts": posts, 
            "has_more": has_more
        }, "Posts retrieved successfully.")
    except ValueError as e:
        return error(str(e), 400)
    except Exception as e:
        print("Get Posts Error:", repr(e))
        return error("Failed to retrieve posts.", 500)

# 在 post_bp.py 中新增
@post_bp.route('/search', methods=['GET'])
def search_posts_by_title():
    """按标题关键词搜索帖子（模糊匹配）"""
    query = request.args.get('q', '').strip()
    if not query:
        return success({"posts": [], "has_more": False}, "No results.")

    # 使用 SQLAlchemy like 模糊查询（不区分大小写）
    posts = Post.query.filter(
        Post.title.ilike(f"%{query}%")
    ).order_by(Post.created_at.desc()).limit(20).all()

    interaction_data = _get_interaction_counts_for_posts(posts)
    serialized_posts = [
        post.to_dict(extra_data=interaction_data.get(post.id, {}))
        for post in posts
    ]
    return success({
        "posts": serialized_posts,
        "has_more": False
    }, "Search completed.")

@post_bp.route('/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(current_user, post_id):
    """删除自己的帖子（需登录）"""
    post = Post.query.get(post_id)
    if not post:
        return error("Post not found.", 404)
    
    if post.user_id != current_user.id and not current_user.is_admin:
        return error("Permission denied.", 403)
    
    try:
        db.session.delete(post)
        db.session.commit()
        return success(None, "Post deleted successfully.")
    except Exception as e:
        db.session.rollback()
        print("Delete Post Error:", repr(e))
        return error("Failed to delete post.", 500)

@post_bp.route('/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """获取帖子详情及其评论，支持评论分页和排序"""
    try:
        comment_sort = request.args.get('comment_sort', 'hot') 
        if comment_sort not in ('hot', 'time_desc'):
            return jsonify({'error': 'Invalid comment_sort. Use: hot, time_desc'}), 400
        limit = request.args.get('limit', default=10, type=int)
        limit = min(max(limit, 1), 200) # 限制 1~200
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
            'post': post,
            'comments': comments,
            'has_more': has_more
        }), 200
    except Exception as e:
        print("Get Post Error:", repr(e))
        return jsonify({'error': 'Failed to load post'}), 500
    
@post_bp.route('/my-posts', methods=['GET'])
@login_required
def get_my_posts(current_user):
    """获取当前用户发布的所有帖子"""
    try:
        # 获取用户所有帖子，按时间倒序
        posts = Post.query.filter_by(user_id=current_user.id) \
                         .order_by(Post.created_at.desc()) \
                         .all()
        interaction_data = _get_interaction_counts_for_posts(posts)
        serialized_posts = [
            post.to_dict(extra_data=interaction_data.get(post.id, {}))
            for post in posts
        ]
        return success(serialized_posts, "My posts retrieved.")
    except Exception as e:
        print("Get My Posts Error:", repr(e))
        return error("Failed to retrieve my posts.", 500)


@post_bp.route('/roam', methods=['GET'])
def get_roam_posts():
    """漫游页：随机获取帖子"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        limit = min(max(limit, 1), 50)  # 限制 1~50

        posts = get_random_posts(limit=limit)

        return success({
            "posts": posts
        }, "Random posts retrieved.")

    except Exception as e:
        print("Roam Posts Error:", repr(e))
        return error("Failed to fetch roam posts.", 500)
    
@post_bp.route('/search-by-tags', methods=['GET'])
def search_posts_by_tags_route():
    """按标签搜索帖子"""
    try:
        # 支持 ?tags=["ai","tech"] 或 tags=ai&tags=tech
        tags_param = request.args.get('tags')
        if tags_param is None:
            return error("Missing 'tags' parameter.", 400)

        # 尝试 JSON 解析（推荐）
        try:
            tags = json.loads(tags_param)
        except (json.JSONDecodeError, TypeError):
            # 回退到多值参数：?tags=ai&tags=tech
            tags = request.args.getlist('tags')

        if not isinstance(tags, list):
            return error("'tags' must be an array of strings.", 400)

        limit = min(max(request.args.get('limit', 10, type=int), 1), 20)
        after_id = request.args.get('after_id', type=int)

        posts, has_more = get_search_posts_by_tags( 
            tag_names=tags,
            limit=limit,
            after_id=after_id
        )

        return success({
            "posts": posts,
            "has_more": has_more
        }, "Posts retrieved successfully.")

    except ValueError as e:
        return error(str(e), 400)
    except Exception as e:
        print("Search Posts Error:", repr(e))
        return error("Failed to search posts.", 500)


@post_bp.route('/<int:post_id>', methods=['PUT'])
@login_required
def update_post(current_user, post_id):
    post = Post.query.get(post_id)
    if not post:
        return error("Post not found.", 404)
    if post.user_id != current_user.id:
        return error("Permission denied.", 403)
    
    data = request.get_json()
    if not data:
        return error("Invalid JSON.", 400)
    
    title = data.get('title')
    content = data.get('content')
    if not title or not content:
        return error("Title and content are required.", 400)

    try:
        post.title = title.strip()
        post.content = content.strip()
        
        # ✅ 正确处理标签
        if 'tags' in data:
            tags_input = data['tags']
            if not isinstance(tags_input, list):
                return error("Tags must be a list.", 400)
            
            # 清洗标签
            cleaned_tags = []
            seen = set()
            for t in tags_input[:5]:  # 最多5个
                s = str(t).strip().lower()
                if s and len(s) <= 15 and s not in seen:
                    cleaned_tags.append(s)
                    seen.add(s)
            
            # 更新关联
            post.tags.clear()
            for tag_name in cleaned_tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                post.tags.append(tag)

        post.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return success(post.to_dict(), "Post updated successfully.")
    except Exception as e:
        db.session.rollback()
        print("Update Post Error:", repr(e))
        return error("Failed to update post.", 500)