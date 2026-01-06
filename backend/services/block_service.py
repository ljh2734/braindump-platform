from database import db
from models import Block, User
from sqlalchemy import and_

def toggle_block(blocker_id: int, blocked_id: int):
    """拉黑或取消拉黑"""
    if blocker_id == blocked_id:
        raise ValueError("不能拉黑自己")

    # 检查用户是否存在
    if not User.query.get(blocked_id):
        raise ValueError("用户不存在")

    # 查询是否已拉黑
    block_record = Block.query.filter_by(
        blocker_id=blocker_id,
        blocked_id=blocked_id
    ).first()

    if block_record:
        # 已拉黑 → 取消
        db.session.delete(block_record)
        db.session.commit()
        return False  # 表示现在未拉黑
    else:
        # 未拉黑 → 创建
        new_block = Block(blocker_id=blocker_id, blocked_id=blocked_id)
        db.session.add(new_block)
        db.session.commit()
        return True   # 表示现在已拉黑

def is_blocked(blocker_id: int, blocked_id: int) -> bool:
    """检查 blocker_id 是否拉黑了 blocked_id"""
    return Block.query.filter_by(
        blocker_id=blocker_id,
        blocked_id=blocked_id
    ).first() is not None

def get_blocked_user_ids(blocker_id: int):
    """获取当前用户拉黑的所有用户ID列表"""
    blocks = Block.query.filter_by(blocker_id=blocker_id).all()
    return [b.blocked_id for b in blocks]