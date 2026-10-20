import os
import pytest
from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic import command
from app.core.config import settings
from app.core.database import check_db_health, engine


def get_alembic_config() -> Config:
    """Helper to locate and build the Alembic configuration."""
    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    config = Config(str(ini_path))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    return config


def test_alembic_configuration_file():
    """Verify that alembic.ini exists and defines the proper script location."""
    config = get_alembic_config()
    assert os.path.exists(config.config_file_name), "alembic.ini not found"
    script_loc = config.get_main_option("script_location")
    assert os.path.isdir(script_loc), f"Script location directory not found: {script_loc}"


def test_alembic_migration_discovery():
    """Verify that Alembic discovers the initial schema revision."""
    config = get_alembic_config()
    script_dir = ScriptDirectory.from_config(config)
    
    revisions = list(script_dir.walk_revisions())
    assert len(revisions) >= 1, "No migration revisions found in alembic/versions"
    
    head_rev = revisions[0]
    assert head_rev.revision == "1333f3d04ff1"
    assert "initial_schema" in head_rev.doc

    # Verify migration module exports upgrade and downgrade
    module = head_rev.module
    assert hasattr(module, "upgrade"), "Migration revision missing upgrade() function"
    assert hasattr(module, "downgrade"), "Migration revision missing downgrade() function"


def test_postgres_live_migration_integration():
    """
    Live PostgreSQL integration test: verifies applying upgrade and downgrade
    against a dedicated, disposable PostgreSQL test database.

    Explicit safeguards:
    - Skipped if PostgreSQL service is offline.
    - Requires target database to explicitly contain 'test' to prevent modifying real databases.
    """
    db_status = check_db_health()
    if db_status.get("status") != "connected":
        pytest.skip(
            "PostgreSQL service is currently offline. Live database migration tests are blocked until PostgreSQL is started."
        )

    # Safeguard check: ensure we do not run migrations against production
    db_name = settings.POSTGRES_DB
    if "test" not in db_name.lower():
        pytest.skip(
            f"Configured database '{db_name}' does not appear to be an isolated test database. "
            "Set DATABASE_URL to a disposable database (e.g. taskflow_test) for live migration rollback testing."
        )

    config = get_alembic_config()

    # 1. Upgrade to head
    command.upgrade(config, "head")

    # 2. Inspect created tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    created_tables = set(inspector.get_table_names())
    expected_tables = {
        "users",
        "projects",
        "project_members",
        "tasks",
        "comments",
        "notifications",
        "activity_logs",
    }
    assert expected_tables.issubset(created_tables)

    # 3. Downgrade to base (clean schema rollback)
    command.downgrade(config, "base")

    # 4. Verify tables removed
    inspector = inspect(engine)
    remaining_tables = set(inspector.get_table_names())
    assert not expected_tables.intersection(remaining_tables)
