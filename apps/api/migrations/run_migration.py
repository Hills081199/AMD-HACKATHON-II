#!/usr/bin/env python3
"""
Run database migrations for Atlas API.
Usage: python migrations/run_migration.py
"""
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.database import engine

def add_generation_duration_column():
    """Add generation_duration_seconds column to topics table if it doesn't exist."""
    with engine.connect() as conn:
        # Check if column exists
        if engine.dialect.name == 'postgresql':
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'topics' AND column_name = 'generation_duration_seconds'
            """))
            exists = result.fetchone() is not None

            if not exists:
                conn.execute(text("""
                    ALTER TABLE topics
                    ADD COLUMN generation_duration_seconds FLOAT
                """))
                conn.commit()
                print("✓ Added generation_duration_seconds column to topics table")
            else:
                print("✓ Column generation_duration_seconds already exists")
        elif engine.dialect.name == 'sqlite':
            # SQLite: check pragma table_info
            result = conn.execute(text("PRAGMA table_info(topics)"))
            columns = [row[1] for row in result.fetchall()]

            if 'generation_duration_seconds' not in columns:
                conn.execute(text("""
                    ALTER TABLE topics
                    ADD COLUMN generation_duration_seconds REAL
                """))
                conn.commit()
                print("✓ Added generation_duration_seconds column to topics table")
            else:
                print("✓ Column generation_duration_seconds already exists")

def main():
    print(f"Running migrations on: {engine.url}")
    add_generation_duration_column()
    print("Migration complete!")

if __name__ == "__main__":
    main()
