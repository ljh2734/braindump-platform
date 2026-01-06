from database import db
from models import Message, User
from sqlalchemy import or_, and_
from services.block_service import is_blocked

def send_message(sender_id: int, receiver_id: int, content: str):
    """发送私信"""
    if sender_id == receiver_id:
        raise ValueError("不能给自己发私信")
    if not content.strip():
        raise ValueError("消息内容不能为空")
    
    # 检查是否被拉黑
    if is_blocked(sender_id, receiver_id):
        raise ValueError("你已拉黑该用户，无法发送消息")
    if is_blocked(receiver_id, sender_id):
        raise ValueError("对方已拉黑你，无法发送消息")

    user_exists = User.query.get(receiver_id)
    if not user_exists:
        raise ValueError("接收用户不存在")
    
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content.strip()
    )
    db.session.add(message)
    db.session.commit()
    return message

def get_conversation(user_id: int, other_id: int, limit=50):
    """获取两人的聊天记录（按时间倒序）"""
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == user_id, Message.receiver_id == other_id),
            and_(Message.sender_id == other_id, Message.receiver_id == user_id)
        )
    ).order_by(Message.created_at.desc()).limit(limit).all()
    return list(reversed(messages))  # 返回从旧到新

def get_contacts_with_last_message(user_id: int):
    """获取联系人列表（含最后一条消息），仅排除拉黑了我的用户"""
    from sqlalchemy import func, case, exists, and_
    from models import Block

    # 子查询：每个对话的最后一条消息ID 和 contact_id
    subq = db.session.query(
        func.max(Message.id).label('last_msg_id'),
        case(
            (Message.sender_id == user_id, Message.receiver_id),
            else_=Message.sender_id
        ).label('contact_id')
    ).filter(
        or_(Message.sender_id == user_id, Message.receiver_id == user_id)
    ).group_by(
        case(
            (Message.sender_id == user_id, Message.receiver_id),
            else_=Message.sender_id
        )
    ).subquery()
    
    # 构建主查询
    query = db.session.query(User, Message)\
        .join(subq, User.id == subq.c.contact_id)\
        .join(Message, Message.id == subq.c.last_msg_id)

    # === 仅过滤：该联系人拉黑了我（blocker_id = 联系人, blocked_id = 我）===
    not_blocked_me = ~exists().where(
        and_(
            Block.blocker_id == User.id,    # 联系人是拉黑者
            Block.blocked_id == user_id     # 拉黑了我
        )
    )
    query = query.filter(not_blocked_me)

    result = query.order_by(Message.created_at.desc()).all()
    
    return [{"user": user.to_public_dict(), "last_message": msg.to_dict()} for user, msg in result]