"""
评论服务层：封装所有与 Comment 相关的业务逻辑
支持嵌套评论、权限控制、批量序列化、级联删除等。
"""

from models import Comment, Post, User, Like, Question
from database import db
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from collections import defaultdict
from datetime import datetime


def _get_all_descendant_ids(comment_id):
    """递归获取某条评论的所有后代评论 ID（深度优先）"""
    ids = []
    children = Comment.query.filter_by(parent_id=comment_id).all()
    for child in children:
        ids.append(child.id)
        ids.extend(_get_all_descendant_ids(child.id))
    return ids


def serialize_comments_with_interactions(comments):
    """
    批量序列化评论列表，避免 N+1 查询（包括 like_count, question_count, author）
    :param comments: List[Comment] —— 假设 author 已通过 joinedload 加载
    :return: List[dict]
    """
    if not comments:
        return []

    comment_ids = [c.id for c in comments]

    # 批量查 like_count
    like_counts = db.session.query(
        Like.target_id,
        db.func.count(Like.id)
    ).filter(
        Like.target_type == 'comment',
        Like.target_id.in_(comment_ids)
    ).group_by(Like.target_id).all()
    like_map = dict(like_counts)

    # 批量查 question_count
    question_counts = db.session.query(
        Question.target_id,
        db.func.count(Question.id)
    ).filter(
        Question.target_type == 'comment',
        Question.target_id.in_(comment_ids)
    ).group_by(Question.target_id).all()
    question_map = dict(question_counts)

    # === 批量查 sub_count（仅对主评论有意义）===
    # 提取所有主评论 ID（即 parent_id 为 None 的评论）
    main_comment_ids = [c.id for c in comments if c.parent_id is None]
    sub_count_map = {}
    if main_comment_ids:
        sub_counts = db.session.query(
            Comment.parent_id,
            db.func.count(Comment.id).label('sub_count')
        ).filter(
            Comment.parent_id.in_(main_comment_ids)
        ).group_by(Comment.parent_id).all()
        sub_count_map = dict(sub_counts)

    result = []
    for c in comments:
        data = {
            'id': c.id,
            'content': c.content,
            'created_at': c.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ") if c.created_at else None,
            'post_id': c.post_id,
            'parent_id': c.parent_id,
            'like_count': like_map.get(c.id, 0),
            'question_count': question_map.get(c.id, 0),
            'author': c.author.to_public_dict(),
            'sub_count': sub_count_map.get(c.id, 0) if c.parent_id is None else 0
        }
        result.append(data)
    return result


def create_comment(post_id, user_id, content, parent_id=None, reply_to_user_id=None):
    """创建评论（支持嵌套和 @ 引用）"""
    if not content.strip():
        return None, "Content is required"

    post = Post.query.get(post_id)
    if not post:
        return None, "Post not found"

    if parent_id is not None:
        parent = Comment.query.filter_by(id=parent_id, post_id=post_id).first()
        if not parent:
            return None, "Parent comment not found or does not belong to this post"

    if reply_to_user_id is not None:
        user_exists = User.query.get(reply_to_user_id) is not None
        if not user_exists:
            return None, "Replied-to user does not exist"

    comment = Comment(
        content=content.strip(),
        post_id=post_id,
        user_id=user_id,
        parent_id=parent_id,
        replied_to_user_id=reply_to_user_id
    )
    try:
        db.session.add(comment)
        db.session.commit()
        return comment, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, "Failed to create comment"


def delete_comment(comment_id, user_id, is_admin=False):
    """删除评论（精细化权限 + 级联删除）"""
    comment = Comment.query.get(comment_id)
    if not comment:
        return False, "Comment not found"

    post = Post.query.get(comment.post_id)
    if not post:
        return False, "Associated post not found"

    can_delete = (
        is_admin or
        comment.user_id == user_id or
        (post.user_id == user_id and comment.parent_id is None)
    )

    if not can_delete:
        return False, "Permission denied"

    all_ids_to_delete = [comment_id]
    all_ids_to_delete.extend(_get_all_descendant_ids(comment_id))

    try:
        Comment.query.filter(Comment.id.in_(all_ids_to_delete)).delete(synchronize_session=False)
        db.session.commit()
        return True, "Comment deleted successfully"
    except SQLAlchemyError:
        db.session.rollback()
        return False, "Failed to delete comment"


def get_comment_tree(post_id):
    """获取帖子的完整嵌套评论树（按时间升序），用于调试或全量导出"""
    comments = Comment.query.options(joinedload(Comment.author)) \
                          .filter_by(post_id=post_id) \
                          .order_by(Comment.created_at).all()

    comment_map = {c.id: c for c in comments}
    children_map = defaultdict(list)
    for c in comments:
        if c.parent_id is not None:
            children_map[c.parent_id].append(c)

    def build_tree(comment):
        base = comment.to_dict()
        base['author'] = comment.author.to_public_dict()
        base['replies'] = [build_tree(child) for child in children_map[comment.id]]
        return base

    top_level = [c for c in comments if c.parent_id is None]
    return [build_tree(c) for c in top_level]


def get_top_level_comment_replies_service(comment_id, limit=10, after=None):
    """
    服务层：获取某顶层评论的分页直接子评论（带完整子树）
    返回: (list_of_replies_dict, has_more, error_message_or_None)
    """
    top_comment = Comment.query.get(comment_id)
    if not top_comment or top_comment.parent_id is not None:
        return None, False, "Top-level comment not found"

    query = Comment.query.options(joinedload(Comment.author)) \
                      .filter_by(parent_id=comment_id) \
                      .order_by(Comment.created_at.asc())
    if after:
        after_dt = datetime.fromisoformat(after.replace('Z', '+00:00'))
        query = query.filter(Comment.created_at < after_dt)

    replies = query.limit(limit + 1).all()
    has_more = len(replies) > limit
    if has_more:
        replies = replies[:-1]

    # 收集所有需要序列化的评论（包括孙子）
    all_ids = set()
    stack = list(replies)
    while stack:
        c = stack.pop()
        all_ids.add(c.id)
        children = Comment.query.filter_by(parent_id=c.id).all()
        stack.extend(children)

    if all_ids:
        all_comments = Comment.query.options(joinedload(Comment.author)) \
                                .filter(Comment.id.in_(all_ids)) \
                                .all()
        serialized_map = {c['id']: c for c in serialize_comments_with_interactions(all_comments)}
    else:
        serialized_map = {}

    def build_subtree(cid):
        data = serialized_map[cid].copy()
        children = Comment.query.filter_by(parent_id=cid).all()
        data['replies'] = [
            build_subtree(child.id) for child in children if child.id in serialized_map
        ]
        return data

    result = [build_subtree(r.id) for r in replies if r.id in serialized_map]
    return result, has_more, None


def _get_interactions_for_comments(comments):
    """
    辅助函数：为评论列表批量获取 like_count 和 question_count
    :param comments: List[Comment]
    :return: Dict[comment_id, {'like_count': int, 'question_count': int}]
    """
    if not comments:
        return {}
    comment_ids = [c.id for c in comments]

    # 批量查 like_count
    like_counts = db.session.query(
        Like.target_id,
        db.func.count(Like.id)
    ).filter(
        Like.target_type == 'comment',
        Like.target_id.in_(comment_ids)
    ).group_by(Like.target_id).all()
    like_map = dict(like_counts)

    # 批量查 question_count
    question_counts = db.session.query(
        Question.target_id,
        db.func.count(Question.id)
    ).filter(
        Question.target_type == 'comment',
        Question.target_id.in_(comment_ids)
    ).group_by(Question.target_id).all()
    question_map = dict(question_counts)

    return {
        cid: {
            'like_count': like_map.get(cid, 0),
            'question_count': question_map.get(cid, 0)
        }
        for cid in comment_ids
    }