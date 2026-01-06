from datetime import datetime, timedelta, timezone
from database import db
from models import Like, Question


def _get_start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def get_sorted_post_ids(sort_type: str, limit: int = 20):
    now = datetime.now(timezone.utc)
    
    if sort_type == 'questions_7d':
        days, interaction_type = 7, 'questions'
    elif sort_type == 'questions_30d':
        days, interaction_type = 30, 'questions'
    elif sort_type == 'interactions_7d':
        days, interaction_type = 7, 'all'
    elif sort_type == 'interactions_30d':
        days, interaction_type = 30, 'all'
    else:
        raise ValueError(f"Unsupported sort_type: {sort_type}")

    cutoff = now - timedelta(days=days)
    cutoff = _get_start_of_day(cutoff)

    if interaction_type == 'questions':
        # 仅统计 Question
        results = db.session.query(
            Question.target_id.label('post_id'),
            db.func.count(Question.id).label('growth')
        ).filter(
            Question.target_type == 'post',
            Question.created_at >= cutoff
        ).group_by(Question.target_id).all()

    else:
        # 分别查 like 和 question 的数量，然后 union all 后 group by
        like_query = db.session.query(
            Like.target_id.label('post_id'),
            db.func.count(Like.id).label('cnt')
        ).filter(
            Like.target_type == 'post',
            Like.created_at >= cutoff
        ).group_by(Like.target_id)

        question_query = db.session.query(
            Question.target_id.label('post_id'),
            db.func.count(Question.id).label('cnt')
        ).filter(
            Question.target_type == 'post',
            Question.created_at >= cutoff
        ).group_by(Question.target_id)

        # 使用 UNION ALL 合并，再外层 GROUP BY SUM
        union_subq = like_query.union_all(question_query).subquery()
        results = db.session.query(
            union_subq.c.post_id,
            db.func.sum(union_subq.c.cnt).label('growth')
        ).group_by(union_subq.c.post_id).all()

    # 排序并返回 post_id 列表
    sorted_items = sorted(results, key=lambda x: x.growth, reverse=True)
    return [item.post_id for item in sorted_items[:limit]]