"""initial initial migration

Revision ID: c222e5a52045
Revises: 20b8540ef38c
Create Date: 2024-12-27 18:28:20.762584

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "c222e5a52045"
down_revision: Union[str, None] = "20b8540ef38c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Pushes changes into the database"""
    # ### commands auto generated by Alembic - please adjust! ###
    # ### end Alembic commands ###


def downgrade() -> None:
    """Reverts changes performed by upgrade"""
    # ### commands auto generated by Alembic - please adjust! ###
    # ### end Alembic commands ###
