"""
This module is used to import all the models in the database.

The models are defined in separate modules to keep the code organized and easy to maintain.
"""

from app.db.database import Base
from .user import User
from .contact import Contact
