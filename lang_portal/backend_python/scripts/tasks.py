from invoke import task
import os
import json
import sqlite3
from pathlib import Path
from typing import Dict, List


def load_seed_file(file_path: str) -> List[Dict]:
    """Load and validate a seed file"""
    with open(file_path) as f:
        data = json.load(f)

    required_fields = {"urdu", "urdlish", "english"}
    for item in data:
        missing = required_fields - set(item.keys())
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

    return data


@task
def init_db(ctx):
    """Initialize the SQLite database"""
    db_path = Path("words.db")
    if db_path.exists():
        print("Database already exists")
        return

    conn = sqlite3.connect(db_path)
    conn.close()
    print("Database initialized")


@task
def migrate(ctx):
    """Run database migrations"""
    migrations_dir = Path("db/migrations")

    # Get all .sql files and sort them
    migration_files = sorted([f for f in migrations_dir.glob("*.sql")])

    conn = sqlite3.connect("words.db")
    for migration_file in migration_files:
        print(f"Running migration: {migration_file}")
        with open(migration_file) as f:
            conn.executescript(f.read())

    conn.close()


@task
def seed_all(ctx):
    """Seed all data files in the seeds directory"""
    seeds_dir = Path("db/seeds")
    seed_configs = {
        "basic_greetings.json": "Basic Greetings",
        # Add more seed files and their group names here
    }

    for seed_file, group_name in seed_configs.items():
        print(f"Seeding {seed_file} into group '{group_name}'...")
        seed(ctx, seed_file, group_name)


@task
def seed(ctx, seed_file: str, group_name: str):
    """Seed data from a specific JSON file"""
    try:
        data = load_seed_file(f"db/seeds/{seed_file}")

        conn = sqlite3.connect("words.db")
        cur = conn.cursor()

        # Create group if it doesn't exist
        cur.execute(
            "INSERT INTO groups (name) VALUES (?) ON CONFLICT(name) DO UPDATE SET name=name RETURNING id",
            (group_name,),
        )
        group_id = cur.fetchone()[0]

        for word in data:
            # Insert word with parts
            parts_json = json.dumps(word.get("parts", {}))
            cur.execute(
                """
                INSERT INTO words (urdu, urdlish, english, parts) 
                VALUES (?, ?, ?, ?)
                RETURNING id
                """,
                (word["urdu"], word["urdlish"], word["english"], parts_json),
            )
            word_id = cur.fetchone()[0]

            # Create word-group association
            cur.execute(
                """
                INSERT INTO words_groups (word_id, group_id) 
                VALUES (?, ?) 
                ON CONFLICT(word_id, group_id) DO NOTHING
                """,
                (word_id, group_id),
            )

        conn.commit()
        print(f"Successfully seeded {len(data)} words into group '{group_name}'")

    except Exception as e:
        conn.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        conn.close()
