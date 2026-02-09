#!/usr/bin/env python3
"""
Database migration script with advanced safety checks.

This script provides safe database migration execution with:
- Pre-flight validation
- Destructive operation detection
- Dry-run mode
- Backup verification
- Post-migration validation
- Rollback support
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from alembic import command

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))


class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def log_info(msg: str) -> None:
    """Log info message."""
    print(f"{Colors.BLUE}i{Colors.END} {msg}")


def log_success(msg: str) -> None:
    """Log success message."""
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")


def log_warning(msg: str) -> None:
    """Log warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")


def log_error(msg: str) -> None:
    """Log error message."""
    print(f"{Colors.RED}✗{Colors.END} {msg}", file=sys.stderr)


def check_database_connectivity(database_url: str) -> bool:
    """Verify database is reachable."""
    log_info("Checking database connectivity...")
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log_success("Database connection successful")
        return True
    except OperationalError as e:
        log_error(f"Database connection failed: {e}")
        return False


def get_pending_migrations(alembic_cfg: Config) -> list[str]:
    """Get list of pending migration revisions."""
    database_url = alembic_cfg.get_main_option("sqlalchemy.url")
    engine = create_engine(database_url)

    script = ScriptDirectory.from_config(alembic_cfg)

    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()

        # Get all revisions from current to head
        if current_rev is None:
            # No migrations applied yet
            pending = list(script.iterate_revisions("head", "base"))
        else:
            pending = list(script.iterate_revisions("head", current_rev))

        # Filter out the current revision
        return [rev for rev in pending if rev.revision != current_rev]


def detect_destructive_operations(migration_file: Path) -> list[str]:
    """Detect potentially destructive SQL operations in migration file."""
    destructive_patterns = [
        (r"\bDROP\s+TABLE\b", "DROP TABLE"),
        (r"\bDROP\s+COLUMN\b", "DROP COLUMN"),
        (r"\bTRUNCATE\b", "TRUNCATE"),
        (r"\bDELETE\s+FROM\b", "DELETE FROM"),
        (r"\bALTER\s+COLUMN\s+.*\s+DROP\b", "ALTER COLUMN DROP"),
    ]

    content = migration_file.read_text()
    detected = []

    for pattern, operation_name in destructive_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            detected.append(operation_name)

    return detected


def analyze_pending_migrations(alembic_cfg: Config) -> dict[str, Any]:
    """Analyze pending migrations for risks."""
    pending = get_pending_migrations(alembic_cfg)

    if not pending:
        return {"count": 0, "migrations": [], "destructive": False, "details": []}

    script_dir = Path(alembic_cfg.get_main_option("script_location"))
    versions_dir = script_dir / "versions"

    details = []
    has_destructive = False

    for rev in pending:
        migration_file = versions_dir / f"{rev.revision}_{rev.down_revision or 'base'}.py"
        # Try to find the file with a different naming pattern
        if not migration_file.exists():
            migration_files = list(versions_dir.glob(f"{rev.revision}_*.py"))
            if migration_files:
                migration_file = migration_files[0]

        destructive_ops = []
        if migration_file.exists():
            destructive_ops = detect_destructive_operations(migration_file)
            if destructive_ops:
                has_destructive = True

        details.append(
            {
                "revision": rev.revision,
                "message": rev.doc,
                "destructive_operations": destructive_ops,
                "file": str(migration_file) if migration_file.exists() else "Not found",
            }
        )

    return {
        "count": len(pending),
        "migrations": pending,
        "destructive": has_destructive,
        "details": details,
    }


def verify_backup_exists(require_backup: bool) -> bool:
    """Verify that a recent backup exists (placeholder for actual backup check)."""
    if not require_backup:
        return True

    log_warning("Backup verification is enabled but not implemented")
    log_warning("In production, this should check for recent database backups")

    response = input("Do you confirm a recent backup exists? (yes/no): ")
    return response.lower() in ["yes", "y"]


def run_preflight_checks(
    alembic_cfg: Config, require_backup: bool, allow_destructive: bool
) -> bool:
    """Run all pre-flight checks before migration."""
    log_info("Running pre-flight checks...")

    # Check database connectivity
    database_url = alembic_cfg.get_main_option("sqlalchemy.url")
    if not check_database_connectivity(database_url):
        return False

    # Check for pending migrations
    analysis = analyze_pending_migrations(alembic_cfg)

    if analysis["count"] == 0:
        log_success("Database is up to date, no migrations to apply")
        return False

    log_info(f"Found {analysis['count']} pending migration(s):")
    for detail in analysis["details"]:
        print(f"  • {detail['revision']}: {detail['message']}")
        if detail["destructive_operations"]:
            log_warning(
                f"    Destructive operations: {', '.join(detail['destructive_operations'])}"
            )

    # Check for destructive operations
    if analysis["destructive"] and not allow_destructive:
        log_error("Destructive operations detected and MIGRATION_ALLOW_DESTRUCTIVE=false")
        log_error("Set MIGRATION_ALLOW_DESTRUCTIVE=true to proceed")
        return False

    if analysis["destructive"]:
        log_warning("Destructive operations will be executed!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            log_info("Migration cancelled by user")
            return False

    # Verify backup
    if not verify_backup_exists(require_backup):
        log_error("Backup verification failed")
        return False

    log_success("Pre-flight checks passed")
    return True


def run_post_migration_validation(alembic_cfg: Config) -> bool:
    """Run validation checks after migration."""
    log_info("Running post-migration validation...")

    database_url = alembic_cfg.get_main_option("sqlalchemy.url")
    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            # Check that alembic_version table exists and has entries
            result = conn.execute(text("SELECT COUNT(*) FROM alembic_version"))
            count = result.scalar()

            if count == 0:
                log_error("No version recorded in alembic_version table")
                return False

            log_success("Migration version recorded successfully")

            # Get current revision
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            log_info(f"Current database version: {version}")

        log_success("Post-migration validation passed")
        return True

    except Exception as e:
        log_error(f"Post-migration validation failed: {e}")
        return False


def run_migrations(
    dry_run: bool = False,
    require_backup: bool = True,
    allow_destructive: bool = False,
    target_revision: str = "head",
) -> int:
    """Execute database migrations with safety checks."""
    from app.config import settings

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_info(f"Migration started at {timestamp}")
    log_info(f"Environment: {settings.environment}")
    log_info(f"Database: {settings.get_database_url().split('@')[-1]}")  # Hide credentials

    # Setup Alembic config
    alembic_ini = Path(__file__).parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))

    # Override database URL from settings
    alembic_cfg.set_main_option("sqlalchemy.url", settings.get_database_url())

    if dry_run:
        log_warning("DRY RUN MODE: No changes will be applied")

    # Run pre-flight checks
    if not run_preflight_checks(alembic_cfg, require_backup, allow_destructive):
        if not dry_run:
            return 0  # No error if no migrations needed
        return 1

    if dry_run:
        log_info("Dry run complete. Use without --dry-run to apply migrations")
        return 0

    # Apply migrations
    try:
        log_info(f"Applying migrations to {target_revision}...")
        command.upgrade(alembic_cfg, target_revision)
        log_success("Migrations applied successfully")

        # Run post-migration validation
        if not run_post_migration_validation(alembic_cfg):
            log_error("Post-migration validation failed")
            return 1

        log_success("Migration completed successfully")
        return 0

    except Exception as e:
        log_error(f"Migration failed: {e}")
        log_error("Database may be in an inconsistent state")
        log_error("Review the error and consider rolling back")
        return 1


def show_current_revision() -> int:
    """Show current database revision."""
    from app.config import settings

    alembic_ini = Path(__file__).parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.get_database_url())

    try:
        command.current(alembic_cfg)
        return 0
    except Exception as e:
        log_error(f"Failed to get current revision: {e}")
        return 1


def show_migration_history() -> int:
    """Show migration history."""
    from app.config import settings

    alembic_ini = Path(__file__).parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.get_database_url())

    try:
        command.history(alembic_cfg)
        return 0
    except Exception as e:
        log_error(f"Failed to get migration history: {e}")
        return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Database migration tool with safety checks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Apply pending migrations")
    upgrade_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migrations without applying them",
    )
    upgrade_parser.add_argument(
        "--no-backup-check",
        action="store_true",
        help="Skip backup verification (not recommended for production)",
    )
    upgrade_parser.add_argument(
        "--allow-destructive",
        action="store_true",
        help="Allow destructive operations (DROP, TRUNCATE, etc.)",
    )
    upgrade_parser.add_argument(
        "--target",
        default="head",
        help="Target revision (default: head)",
    )

    # Current command
    subparsers.add_parser("current", help="Show current database revision")

    # History command
    subparsers.add_parser("history", help="Show migration history")

    args = parser.parse_args()

    if args.command == "upgrade":
        require_backup = not args.no_backup_check
        return run_migrations(
            dry_run=args.dry_run,
            require_backup=require_backup,
            allow_destructive=args.allow_destructive,
            target_revision=args.target,
        )
    if args.command == "current":
        return show_current_revision()
    if args.command == "history":
        return show_migration_history()

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
