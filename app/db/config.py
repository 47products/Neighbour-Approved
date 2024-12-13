"""
Database configuration module. 

This module defines the database configuration settings using Pydantic's BaseSettings class.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    ## Database Configuration Settings.

    This class defines the database configuration settings using Pydantic's BaseSettings class.

    ### Attributes:
    - **DATABASE_URL:** The database connection URL.

    ### Example:
    ```python
    settings = Settings()
    print(settings.DATABASE_URL)
    ```

    ### Environment Variables:
    - **DATABASE_URL:** The database connection URL.

    ### Default Values:
    - **DATABASE_URL:** `sqlite:///./app.db`

    ### Example:
    ```bash
    DATABASE_URL=sqlite:///./app.db
    ```

    ### Note:
    The `DATABASE_URL` environment variable should be set to the database connection URL.

    ### See Also:
    - [Pydantic BaseSettings](https://pydantic-docs.helpmanual.io/usage/settings
    )

    ### References:
    - [Pydantic BaseSettings](https://pydantic-docs.helpmanual.io/usage/settings)
    - [FastAPI Configuration](https://fastapi.tiangolo.com/advanced/settings/)
    """

    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    POSTGRES_HOST: str = Field(..., env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(..., env="POSTGRES_PORT")
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    class Config:
        """Configuration settings for the Settings class."""

        env_file = ".env"
