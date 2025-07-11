"""Set native_enum to False for status fields

Revision ID: 3818f7ceabb7
Revises: 217103290d51
Create Date: 2025-06-24 12:23:54.500407

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3818f7ceabb7'
down_revision: Union[str, None] = '217103290d51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('contracts', 'contract_status',
               existing_type=postgresql.ENUM('DRAFT', 'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'COMPLETED', name='contractstatus'),
               type_=sa.Enum('DRAFT', 'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'COMPLETED', name='contractstatus', native_enum=False),
               existing_nullable=False)
    op.alter_column('contracts', 'payment_status',
               existing_type=postgresql.ENUM('UNPAID', 'PREPARED', 'OVERDUE', 'PAID', 'REFUNDED', 'CANCELLED', name='paymentstatus'),
               type_=sa.Enum('UNPAID', 'PARTIAL', 'PREPARED', 'OVERDUE', 'PAID', 'REFUNDED', 'CANCELLED', name='paymentstatus', native_enum=False),
               existing_nullable=False)
    op.create_index(op.f('ix_contracts_title'), 'contracts', ['title'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_contracts_title'), table_name='contracts')
    op.alter_column('contracts', 'payment_status',
               existing_type=sa.Enum('UNPAID', 'PARTIAL', 'PREPARED', 'OVERDUE', 'PAID', 'REFUNDED', 'CANCELLED', name='paymentstatus', native_enum=False),
               type_=postgresql.ENUM('UNPAID', 'PREPARED', 'OVERDUE', 'PAID', 'REFUNDED', 'CANCELLED', name='paymentstatus'),
               existing_nullable=False)
    op.alter_column('contracts', 'contract_status',
               existing_type=sa.Enum('DRAFT', 'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'COMPLETED', name='contractstatus', native_enum=False),
               type_=postgresql.ENUM('DRAFT', 'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'COMPLETED', name='contractstatus'),
               existing_nullable=False)
    # ### end Alembic commands ###
