#!/usr/bin/env python3
"""Database setup and migration script for callback-mcp-server."""
import logging
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from database import DatabaseStore, Base

logging.basicConfig(
    level="INFO",
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def setup_database():
    """Initialize database with tables."""
    try:
        logger.info(f"Connecting to database: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
        store = DatabaseStore(config.DATABASE_URL, echo=False)
        
        if store.health_check():
            logger.info("✓ Database connection successful")
        else:
            logger.error("✗ Database connection failed")
            return False
        
        logger.info("✓ Database tables initialized successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")
        logger.error(f"  Make sure PostgreSQL is running and database '{config.DB_NAME}' exists")
        return False


def create_database(host: str, port: int, user: str, password: str, dbname: str):
    """Create PostgreSQL database."""
    try:
        import psycopg2
        
        logger.info(f"Attempting to create database '{dbname}'...")
        
        # Connect to default 'postgres' database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Try to create database (safely quoting the name)
        try:
            # Use standard SQL with quoted identifier
            cursor.execute(f'CREATE DATABASE "{dbname}"')
            logger.info(f"✓ Database '{dbname}' created successfully")
        except psycopg2.errors.DuplicateDatabase:
            logger.info(f"✓ Database '{dbname}' already exists")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"✗ Failed to create database: {e}")
        logger.info("Troubleshooting:")
        logger.info("  - Verify PostgreSQL is running")
        logger.info("  - Check that you have superuser permissions")
        logger.info("  - Try connecting manually: psql -h {} -U {} -d postgres".format(host, user))
        logger.info("  - If database exists, just run: python setup_db.py --migrate")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup and manage callback-mcp-server database"
    )
    parser.add_argument(
        "--create-db",
        action="store_true",
        help="Create the PostgreSQL database (requires superuser credentials)"
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Initialize tables in existing database"
    )
    parser.add_argument(
        "--full-setup",
        action="store_true",
        help="Create database and initialize tables (full setup)"
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not (args.create_db or args.migrate or args.full_setup):
        parser.print_help()
        print("\nCurrent Configuration:")
        print(config)
        return 1
    
    success = True
    
    if args.create_db or args.full_setup:
        logger.info("=" * 60)
        logger.info("Creating PostgreSQL Database")
        logger.info("=" * 60)
        success = create_database(
            config.DB_HOST,
            config.DB_PORT,
            config.DB_USER,
            config.DB_PASSWORD,
            config.DB_NAME
        )
        
        if not success:
            return 1
    
    if args.migrate or args.full_setup:
        logger.info("=" * 60)
        logger.info("Initializing Database Tables")
        logger.info("=" * 60)
        success = setup_database()
        
        if not success:
            return 1
    
    if success:
        logger.info("=" * 60)
        logger.info("✓ Database setup completed successfully")
        logger.info("=" * 60)
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
