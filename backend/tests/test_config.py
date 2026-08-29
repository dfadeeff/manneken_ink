import pytest

from app.config import Settings


@pytest.mark.parametrize(
    "given, expected",
    [
        # Railway and Heroku hand out sync URLs; asyncpg is what we actually need.
        ("postgresql://u:p@host:5432/db", "postgresql+asyncpg://u:p@host:5432/db"),
        ("postgres://u:p@host:5432/db", "postgresql+asyncpg://u:p@host:5432/db"),
        # Already-async and non-Postgres URLs are left alone.
        ("postgresql+asyncpg://u:p@host/db", "postgresql+asyncpg://u:p@host/db"),
        ("sqlite+aiosqlite:///./manneken.db", "sqlite+aiosqlite:///./manneken.db"),
    ],
)
def test_database_url_is_normalised_to_an_async_driver(given, expected):
    assert Settings(database_url=given, _env_file=None).database_url == expected


def test_dev_auth_bypass_cannot_be_enabled_in_production():
    with pytest.raises(ValueError, match="only allowed when ENVIRONMENT=development"):
        Settings(environment="production", dev_auth_bypass=True, _env_file=None)

    # ...and is allowed in development.
    assert Settings(environment="development", dev_auth_bypass=True, _env_file=None).dev_auth_bypass
