# backend/services/post_service.py
"""帖子服务层：封装所有与 Post 相关的业务逻辑"""

from datetime import datetime, timedelta, timezone
from database import db
from models import Post, Comment, Like, Question
from services.comment_service import (
    _get_all_descendant_ids,
    serialize_comments_with_interactions,
    _get_interactions_for_comments
)
from sqlalchemy.orm import joinedload
from sqlalchemy import case, func
from services.analytics_service import get_sorted_post_ids

# backend/services/post_service.py

def create_post(user_id, title, content, tags=None):
    if not title or not title.strip():
        raise ValueError("Title cannot be empty.")
    if not content or not content.strip():
        raise ValueError("Content cannot be empty.")
    
    # 标签处理与校验
    if tags is None:
        tags = []
    if not isinstance(tags, list):
        raise ValueError("Tags must be a list of strings.")

    cleaned_tags = []
    for t in tags:
        # 转为字符串并去除首尾空格
        s = str(t).strip()
        # 跳过空字符串
        if not s:
            continue
        # 检查长度：1 ~ 15 个字符
        if len(s) < 1:
            continue  # 实际不会发生，因 strip 后非空
        if len(s) > 15:
            raise ValueError(f"Tag '{s}' exceeds 15 characters.")
        cleaned_tags.append(s)

    # 去重
    seen = set()
    unique_tags = []
    for tag in cleaned_tags:
        if tag not in seen:
            unique_tags.append(tag)
            seen.add(tag)
    cleaned_tags = unique_tags[:10]  # 最多保留10个

    # 强制至少一个有效标签
    if not cleaned_tags:
        raise ValueError("At least one valid tag (1–15 characters) is required.")

    # 创建帖子
    post = Post(
        title=title.strip(),
        content=content.strip(),
        user_id=user_id,
        tags=cleaned_tags
    )
    db.session.add(post)
    db.session.commit()
    db.session.refresh(post)
    return post


def get_all_posts():
    """获取所有帖子（按时间倒序）"""
    posts = Post.query.order_by(Post.created_at.desc()).all()
    interaction_data = _get_interaction_counts_for_posts(posts)
    for post in posts:
        post.like_count = interaction_data[post.id]['like_count']
        post.question_count = interaction_data[post.id]['question_count']
        post.comment_count = interaction_data[post.id]['comment_count']
    return posts



def get_post_with_paginated_comments(post_id, limit=10, before=None, after=None, sort='hot'):
    """
    获取帖子及分页的顶层评论
    :param sort: 'hot' (default) or 'time_desc'
    """
    post = Post.query.get(post_id)
    if not post:
        return None, [], False

    if sort == 'time_desc':
        # 按时间倒序（最新在上）
        query = Comment.query.options(joinedload(Comment.author)) \
                          .filter_by(post_id=post_id, parent_id=None) \
                          .order_by(Comment.created_at.desc())
        if after:
            after_dt = datetime.fromisoformat(after.replace('Z', '+00:00'))
            query = query.filter(Comment.created_at < after_dt)  # 加载更旧的
        top_level_comments = query.limit(limit + 1).all()
        has_more = len(top_level_comments) > limit
        if has_more:
            top_level_comments = top_level_comments[:-1]

    elif sort == 'hot':
        # 先获取所有顶层评论（不分页），再内存排序
        all_top_comments = Comment.query.options(joinedload(Comment.author)) \
                                   .filter_by(post_id=post_id, parent_id=None) \
                                   .all()
        if not all_top_comments:
            return post, [], False

        # 批量获取互动数据用于排序
        serialized_map = _get_interactions_for_comments(all_top_comments)
        sorted_comments = sorted(
            all_top_comments,
            key=lambda c: (
                -(serialized_map[c.id]['like_count'] + serialized_map[c.id]['question_count']),
                -c.created_at.timestamp()  # 时间辅助（越新越前）
            )
        )
        top_level_comments = sorted_comments[:limit]
        has_more = len(sorted_comments) > limit

    else:
        raise ValueError("Invalid sort parameter")

    # === 以下逻辑通用（构建 top_reply + total_descendants）===
    if not top_level_comments:
        return post, [], has_more

    # 收集所有需要序列化的评论（顶层 + 后代）
    all_comments_to_serialize = list(top_level_comments)
    all_descendant_ids = set()
    for top in top_level_comments:
        all_descendant_ids.update(_get_all_descendant_ids(top.id))

    if all_descendant_ids:
        descendants = Comment.query.options(joinedload(Comment.author)) \
                               .filter(Comment.id.in_(all_descendant_ids)) \
                               .all()
        all_comments_to_serialize.extend(descendants)

    serialized_map_full = {
        c['id']: c for c in serialize_comments_with_interactions(all_comments_to_serialize)
    }

    def build_tree_from_serialized(cid):
        data = serialized_map_full[cid].copy()
        children = Comment.query.filter_by(parent_id=cid).all()
        data['replies'] = [
            build_tree_from_serialized(child.id) for child in children if child.id in serialized_map_full
        ]
        return data

    result_comments = []
    for top in top_level_comments:
        direct_children = Comment.query.filter_by(parent_id=top.id).all()
        hottest = None
        if direct_children:
            # 注意：这里仍用 full map 中的数据排序
            sorted_children = sorted(
                direct_children,
                key=lambda x: (
                    -(serialized_map_full[x.id]['like_count'] + serialized_map_full[x.id]['question_count']),
                    x.created_at
                )
            )
            hottest = build_tree_from_serialized(sorted_children[0].id)

        top_data = serialized_map_full[top.id].copy()
        top_data['top_reply'] = hottest
        top_data['total_descendants'] = len(_get_all_descendant_ids(top.id))
        top_data.pop('replies', None)
        result_comments.append(top_data)

    if post:
        interaction_data = _get_interaction_counts_for_posts([post])
        post.like_count = interaction_data[post.id]['like_count']
        post.question_count = interaction_data[post.id]['question_count']
        post.comment_count = interaction_data[post.id]['comment_count']
        
    return post, result_comments, has_more

def get_posts_paginated_by_sort(sort_type='newest', limit=10, before=None, after=None):
    """
    根据排序类型获取分页帖子（支持 newest, questions_7d, interactions_30d 等）
    注意：增长类排序不分页（因需全量计算），仅支持 limit 控制数量
    """
    valid_sorts = ['newest', 'questions_7d', 'questions_30d', 'interactions_7d', 'interactions_30d']
    if sort_type not in valid_sorts:
        raise ValueError("Invalid sort_type")

    if sort_type == 'newest':
        query = Post.query.order_by(Post.created_at.desc())
        if after:
            after_dt = datetime.fromisoformat(after.replace('Z', '+00:00'))
            query = query.filter(Post.created_at < after_dt)
        posts = query.limit(limit + 1).all()
        has_more = len(posts) > limit
        if has_more:
            posts = posts[:-1]
        

        interaction_data = _get_interaction_counts_for_posts(posts)
        for post in posts:
            post.like_count = interaction_data[post.id]['like_count']
            post.question_count = interaction_data[post.id]['question_count']
            post.comment_count = interaction_data[post.id]['comment_count']
        return posts, has_more

    else:
        post_ids = get_sorted_post_ids(sort_type=sort_type, limit=limit)
        if not post_ids:
            return [], False
        posts = Post.query.filter(Post.id.in_(post_ids)).all()
        post_map = {p.id: p for p in posts}
        ordered_posts = [post_map[pid] for pid in post_ids if pid in post_map]
        
        # 注入互动数据
        interaction_data = _get_interaction_counts_for_posts(ordered_posts)
        for post in ordered_posts:
            post.like_count = interaction_data[post.id]['like_count']
            post.question_count = interaction_data[post.id]['question_count']
            post.comment_count = interaction_data[post.id]['comment_count']
        has_more = False # 增长类排序不支持分页
        return ordered_posts, has_more
    

def get_random_posts(limit=10):
    """获取最近30天内的随机帖子"""
    if limit <= 0:
        return []
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    #计算30天前时间
    posts = Post.query.filter(Post.created_at >= thirty_days_ago).order_by(func.random()).limit(limit).all()  
    # 批量注入互动数据
    interaction_data = _get_interaction_counts_for_posts(posts)
    for post in posts:
        post.like_count = interaction_data[post.id]['like_count']
        post.question_count = interaction_data[post.id]['question_count']
        post.comment_count = interaction_data[post.id]['comment_count']
    return posts


def _get_interaction_counts_for_posts(posts):
    """
    批量获取多个 Post 的：
    - like_count
    - question_count
    - comment_count
    """
    if not posts:
        return {}

    post_ids = [p.id for p in posts]

    # 1. 点赞数
    like_counts = db.session.query(
        Like.target_id,
        func.count(Like.id)
    ).filter(
        Like.target_type == 'post',
        Like.target_id.in_(post_ids)
    ).group_by(Like.target_id).all()
    like_map = dict(like_counts)

    # 2. 问号数
    question_counts = db.session.query(
        Question.target_id,
        func.count(Question.id)
    ).filter(
        Question.target_type == 'post',
        Question.target_id.in_(post_ids)
    ).group_by(Question.target_id).all()
    question_map = dict(question_counts)

    # 3. 评论数
    comment_counts = db.session.query(
        Comment.post_id,
        func.count(Comment.id)
    ).filter(
        Comment.post_id.in_(post_ids)
    ).group_by(Comment.post_id).all()
    comment_map = dict(comment_counts)

    return {
        pid: {
            'like_count': like_map.get(pid, 0),
            'question_count': question_map.get(pid, 0),
            'comment_count': comment_map.get(pid, 0)
        }
        for pid in post_ids
    }