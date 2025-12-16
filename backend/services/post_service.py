# backend/services/post_service.py
"""帖子服务层：封装所有与 Post 相关的业务逻辑"""

from datetime import datetime, timedelta, timezone
from database import db
from models import Post, Comment, Like, Question, Tag, post_tags
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
    
    # 校验 tags
    if tags is None:
        tags = []
    if not isinstance(tags, list):
        raise ValueError("Tags must be a list of strings.")

    cleaned_tags = []
    for t in tags:
        s = str(t).strip()
        if not s:
            continue
        if len(s) > 15:
            raise ValueError(f"Tag '{s}' exceeds 15 characters.")
        # 统一小写（避免 "AI" 和 "ai" 分离）
        s = s.lower()
        if s not in cleaned_tags:  # 内存去重
            cleaned_tags.append(s)

    if not cleaned_tags:
        raise ValueError("At least one valid tag (1–15 characters) is required.")
    if len(cleaned_tags) > 10:
        cleaned_tags = cleaned_tags[:10]

    # 创建帖子
    post = Post(
        title=title.strip(),
        content=content.strip(),
        user_id=user_id
    )
    db.session.add(post)
    db.session.flush()  # 获取 post.id

    # 处理标签
    tag_objects = []
    for tag_name in cleaned_tags:
        # 查找或创建 Tag
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
            db.session.flush()
        tag_objects.append(tag)
    
    post.tags = tag_objects
    db.session.commit()
    db.session.refresh(post)
    return post


def get_all_posts():
    """获取所有帖子（按时间倒序）"""
    posts = Post.query.order_by(Post.created_at.desc()).all()
    interaction_data = _get_interaction_counts_for_posts(posts)
    # 直接返回带 extra_data 的字典列表
    return [post.to_dict(extra_data=interaction_data[post.id]) for post in posts]



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

    interaction_data = {}
    if post:
        interaction_data = _get_interaction_counts_for_posts([post])

    if post:
        post_dict = post.to_dict(extra_data=interaction_data[post.id])
    else:
        post_dict = None
    return post_dict, result_comments, has_more

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
        # 返回字典列表 + has_more
        return [
            post.to_dict(extra_data=interaction_data[post.id]) for post in posts
        ], has_more

    else:
        post_ids = get_sorted_post_ids(sort_type=sort_type, limit=limit)
        if not post_ids:
            return [], False
        posts = Post.query.filter(Post.id.in_(post_ids)).all()
        post_map = {p.id: p for p in posts}
        ordered_posts = [post_map[pid] for pid in post_ids if pid in post_map]
        
        # 注入互动数据
        interaction_data = _get_interaction_counts_for_posts(ordered_posts)
        return [post.to_dict(extra_data=interaction_data[post.id]) for post in ordered_posts], has_more
    

def get_random_posts(limit=10):
    """获取最近30天内的随机帖子"""
    if limit <= 0:
        return []
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    #计算30天前时间
    posts = Post.query.filter(Post.created_at >= thirty_days_ago).order_by(func.random()).limit(limit).all()  
    interaction_data = _get_interaction_counts_for_posts(posts)
    return [post.to_dict(extra_data=interaction_data[post.id]) for post in posts]

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

def search_posts_by_tags(tag_names, limit=10, after_id=None):
    """
    按标签搜索帖子：
    - tag_names: ['ai', '科技'] （应为小写）
    - 返回匹配至少一个标签的帖子
    - 按匹配标签数 DESC, created_at DESC 排序
    - 支持游标分页（after_id）
    """
    if not tag_names or limit <= 0:
        return [], False

    # 转小写 + 去重
    tag_names = list(set([name.strip().lower() for name in tag_names if name.strip()]))
    if not tag_names:
        return [], False

    # 查询存在的 tag_ids
    existing_tags = Tag.query.filter(Tag.name.in_(tag_names)).all()
    if not existing_tags:
        return [], False
    tag_ids = [t.id for t in existing_tags]

    # 构建查询：JOIN 中间表，GROUP BY 计算匹配数
    query = (
        db.session.query(Post, func.count(post_tags.c.tag_id).label('match_count'))
        .join(post_tags, Post.id == post_tags.c.post_id)
        .filter(post_tags.c.tag_id.in_(tag_ids))
        .group_by(Post.id)
        .order_by(func.count(post_tags.c.tag_id).desc(), Post.created_at.desc())
    )

    # 游标分页：只加载比 after_id 更早的帖子（按排序规则）
    if after_id is not None:
        # 找到 after_id 对应的帖子的 (match_count, created_at)
        after_post = Post.query.get(after_id)
        if after_post:
            after_match_count = (
                db.session.query(func.count(post_tags.c.tag_id))
                .filter(post_tags.c.post_id == after_id, post_tags.c.tag_id.in_(tag_ids))
                .scalar()
            )
            # 条件：匹配数更少，或匹配数相同但创建时间更早
            query = query.filter(
                (func.count(post_tags.c.tag_id) < after_match_count) |
                ((func.count(post_tags.c.tag_id) == after_match_count) & (Post.created_at < after_post.created_at))
            )

    # 执行查询
    results = query.limit(limit + 1).all()
    posts = [r[0] for r in results]
    has_more = len(posts) > limit
    if has_more:
        posts = posts[:-1]

    interaction_data = _get_interaction_counts_for_posts(posts)
    return [
        post.to_dict(extra_data=interaction_data[post.id]) for post in posts
    ], has_more