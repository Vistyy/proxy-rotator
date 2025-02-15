"""create proxy tables

Revision ID: 256617ed0e96
Revises: 
Create Date: 2025-02-15 16:02:42.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '256617ed0e96'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create proxy_sources table
    op.create_table('proxy_sources',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('url', sa.String(), nullable=False),
                    sa.Column('enabled', sa.Boolean(), nullable=True),
                    sa.Column('last_fetch', sa.DateTime(), nullable=True),
                    sa.Column('fetch_interval', sa.Integer(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('url')
                    )

    # Create proxies table
    op.create_table('proxies',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('address', sa.String(), nullable=False),
                    sa.Column('protocol', sa.String(), nullable=False),
                    sa.Column('source_id', sa.Integer(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('last_checked', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('address'),
                    sa.ForeignKeyConstraint(['source_id'], ['proxy_sources.id'])
                    )

    # Create proxy_stats table
    op.create_table('proxy_stats',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('proxy_id', sa.Integer(), nullable=True),
                    sa.Column('success_count', sa.Integer(), nullable=True),
                    sa.Column('failure_count', sa.Integer(), nullable=True),
                    sa.Column('last_success', sa.DateTime(), nullable=True),
                    sa.Column('last_failure', sa.DateTime(), nullable=True),
                    sa.Column('last_check', sa.DateTime(), nullable=True),
                    sa.Column('average_response_time', sa.Float(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.ForeignKeyConstraint(['proxy_id'], ['proxies.id'])
                    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('proxy_stats')
    op.drop_table('proxies')
    op.drop_table('proxy_sources')
