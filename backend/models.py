from datetime import datetime, timezone
from database import db
from werkzeug.security import generate_password_hash, check_password_hash

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15), unique=True, nullable=False)  # 1~15字符，小写存储

    def __repr__(self):
        return f"<Tag {self.name}>"
    
post_tags = db.Table(
    'post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    avatar_url = db.Column(db.String(256))

    # 用户发布的脑洞
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    # 用户发表的评论
    comments = db.relationship('Comment', foreign_keys='Comment.user_id', back_populates='author', lazy=True, cascade='all, delete-orphan')
    # 用户点赞记录
    likes = db.relationship('Like', foreign_keys='Like.user_id', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
            """完整用户信息（用于本人或管理员）"""
            return {
                'id': self.id,
                'email': self.email,
                'username': self.username,
                'is_admin': self.is_admin,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'avatar_url': self.avatar_url or "/static/default-avatar.png"
            }

    def to_public_dict(self):
        """公开用户信息（用于作者展示、他人查看）"""
        return {
            'id': self.id,
            'username': self.username,
            'avatar_url': self.avatar_url or "/static/default-avatar.png"
        }
   


class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    tags = db.Column(db.JSON, nullable=True, default=list)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc),index = True)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    # 外键：作者
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @property
    def like_count(self):
        return Like.query.filter_by(target_type='post', target_id=self.id).count()

    @property
    def question_count(self):
        return Question.query.filter_by(target_type='post', target_id=self.id).count()

    # 评论关系
    comments = db.relationship(
        'Comment',
        foreign_keys='Comment.post_id',
        back_populates='post',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    # 关联tag
    tags = db.relationship('Tag', secondary=post_tags, lazy='joined', backref=db.backref('posts', lazy=True))

    def to_dict(self, extra_data=None):
        extra_data = extra_data or {}
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'author': self.author.to_public_dict(),
            'comment_count': extra_data.get('comment_count', len(self.comments)),  # 安全回退
            'tags': [tag.name for tag in self.tags],
            'like_count': extra_data.get('like_count', self.like_count),
            'question_count': extra_data.get('question_count', self.question_count)
        }


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    replied_to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 被 @ 的人（可为空）
 
    # 关系
    author = db.relationship('User', foreign_keys=[user_id], back_populates='comments')
    post = db.relationship('Post', foreign_keys=[post_id], back_populates='comments')

    def to_dict(self):
        from models import Like, Question
        like_count = Like.query.filter_by(target_type='comment', target_id=self.id).count()
        question_count = Question.query.filter_by(target_type='comment', target_id=self.id).count()
        
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'author': self.author.to_public_dict(),
            'post_id': self.post_id,
            'parent_id': self.parent_id,
            'like_count': like_count,          
            'question_count': question_count 
        }
    
    def get_replies_paginated(self, limit=1, offset=0):
        """获取该评论的直接子回复（分页），按创建时间升序（最早在上）"""
        return Comment.query.filter_by(parent_id=self.id) \
                            .order_by(Comment.created_at.asc()) \
                            .offset(offset).limit(limit).all()

    def get_total_reply_count(self):
        """获取该评论的总回复数"""
        return Comment.query.filter_by(parent_id=self.id).count()

    __table_args__ = (
        db.Index('idx_comment_post_parent_created', 'post_id', 'parent_id', 'created_at'),
    )

# ====== 互动模型（支持 Post 和 Comment） ======

class Like(db.Model):
    __tablename__ = 'like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_type = db.Column(db.String(20), nullable=False)  # 'post' or 'comment'
    target_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # 确保一个用户不能重复对同一目标点赞
    __table_args__ = (
        db.UniqueConstraint('user_id', 'target_type', 'target_id', name='uq_like_user_target'),
        db.Index('idx_like_target', 'target_type', 'target_id')
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Question(db.Model):
    """表示用户对某内容点‘问号’（表达困惑、质疑等）"""
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_type = db.Column(db.String(20), nullable=False)  # 'post' or 'comment'
    target_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # 确保一个用户不能重复对同一目标点问号
    __table_args__ = (
        db.UniqueConstraint('user_id', 'target_type', 'target_id', name='uq_question_user_target'),
        db.Index('idx_question_target', 'target_type', 'target_id')
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }