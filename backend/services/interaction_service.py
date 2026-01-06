"""
互动服务模块：处理点赞（Like）和问号（Question）操作。
支持对 Post 或 Comment 进行独立的 Like / Question 操作。
每个操作都是“切换”行为：不存在则创建，存在则删除。
"""

from database import db
from models import Like, Question


def _toggle_action(model_class, user_id: int, target_type: str, target_id: int):
    """
    通用切换操作函数。
    
    :param model_class: Like 或 Question 类
    :param user_id: 当前用户 ID
    :param target_type: 'post' 或 'comment'
    :param target_id: 目标对象 ID
    :return: (success: bool, is_active_after: bool, new_count: int)
    """
    try:
        # 查找是否已存在该用户的操作记录
        existing = model_class.query.filter_by(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id
        ).first()

        if existing:
            # 已存在 → 取消操作（删除记录）
            db.session.delete(existing)
            db.session.commit()
            is_active = False
        else:
            # 不存在 → 创建新记录
            new_action = model_class(
                user_id=user_id,
                target_type=target_type,
                target_id=target_id
            )
            db.session.add(new_action)
            db.session.commit()
            is_active = True

        # 计算当前目标的总互动数（实时 COUNT，无需缓存字段）
        count = model_class.query.filter_by(
            target_type=target_type,
            target_id=target_id
        ).count()

        return True, is_active, count

    except Exception as e:
        db.session.rollback()
        # 记录日志
        print(f"Error in _toggle_action: {e}")
        return False, False, 0


def toggle_like(user_id: int, target_type: str, target_id: int):
    """
    切换点赞状态。
    示例：
      - 用户未点赞 → 点赞成功，返回 (True, True, 新数量)
      - 用户已点赞 → 取消点赞，返回 (True, False, 新数量)
    """
    return _toggle_action(Like, user_id, target_type, target_id)


def toggle_question(user_id: int, target_type: str, target_id: int):
    """
    切换问号状态。
    行为同 toggle_like，但作用于 Question 表。
    """
    return _toggle_action(Question, user_id, target_type, target_id)


def get_interaction_status(user_id: int, target_type: str, target_id: int):
    """
    获取用户对某目标的互动状态及总数。
    
    返回示例：
    {
        'has_liked': True,
        'has_questioned': False,
        'like_count': 5,
        'question_count': 2
    }
    """
    # 查询用户是否已点赞
    has_liked = Like.query.filter_by(
        user_id=user_id,
        target_type=target_type,
        target_id=target_id
    ).first() is not None

    # 查询用户是否已点问号
    has_questioned = Question.query.filter_by(
        user_id=user_id,
        target_type=target_type,
        target_id=target_id
    ).first() is not None

    # 统计总数
    like_count = Like.query.filter_by(
        target_type=target_type,
        target_id=target_id
    ).count()

    question_count = Question.query.filter_by(
        target_type=target_type,
        target_id=target_id
    ).count()

    return {
        'has_liked': has_liked,
        'has_questioned': has_questioned,
        'like_count': like_count,
        'question_count': question_count
    }