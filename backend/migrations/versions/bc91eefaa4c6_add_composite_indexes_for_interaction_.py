"""add composite indexes for interaction time queries

Revision ID: bc91eefaa4c6
Revises: 8d9609d76a5d
Create Date: 2025-12-11

"""
from alembic import op
import sqlalchemy as sa

# 必须显式声明这两个变量（Flask-Migrate 需要）
revision = 'bc91eefaa4c6'
down_revision = '8d9609d76a5d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        'idx_like_target_created',
        'like',
        ['target_type', 'target_id', 'created_at']
    )
    op.create_index(
        'idx_question_target_created',
        'question',
        ['target_type', 'target_id', 'created_at']
    )


def downgrade():
    op.drop_index('idx_like_target_created', table_name='like')
    op.drop_index('idx_question_target_created', table_name='question')