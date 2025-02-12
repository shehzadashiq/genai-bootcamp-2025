from invoke import task
import os
import json
from pathlib import Path
import sys


def set_django_env():
    """Set environment variables for Django"""
    os.environ["PYTHONPATH"] = "."
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_test"


@task
def init_db(ctx):
    """Initialize the SQLite database"""
    print("Initializing database...")
    ctx.run("python scripts/manage.py migrate")


@task
def migrate(ctx):
    """Run database migrations"""
    print("Running migrations...")
    ctx.run("python scripts/manage.py migrate")


@task
def seed_data(ctx, file_path=None, group_name=None):
    """
    Import seed data from JSON files
    Usage: invoke seed-data --file-path=path/to/file.json --group-name="Basic Words"
    """
    if not file_path or not group_name:
        print("Please provide both file_path and group_name")
        print(
            "Usage: invoke seed-data --file-path=path/to/file.json --group-name='Basic Words'"
        )
        return

    print(f"Seeding data from {file_path} into group '{group_name}'...")
    ctx.run(f'python scripts/manage.py seed_data "{file_path}" "{group_name}"')


@task
def seed_all(ctx):
    """Seed all initial data from the seeds directory"""
    # First, ensure migrations are run
    print("Running migrations first...")
    ctx.run("python scripts/manage.py migrate")

    seeds_dir = Path("db/seeds")
    if not seeds_dir.exists():
        print("Seeds directory not found!")
        return

    seed_groups = {
        "basic_words.json": "Basic Words",
        "greetings.json": "Greetings",
        "numbers.json": "Numbers",
        "colors.json": "Colors",
        "family.json": "Family",
    }

    for seed_file, group_name in seed_groups.items():
        file_path = seeds_dir / seed_file
        if file_path.exists():
            print(f"Seeding {seed_file} into {group_name}...")
            ctx.run(f'python scripts/manage.py seed_data "{file_path}" "{group_name}"')
        else:
            print(f"Warning: {seed_file} not found, skipping...")


@task
def runserver(ctx, port=8000):
    """Run the development server"""
    print(f"Starting development server on port {port}...")
    ctx.run(f"python scripts/manage.py runserver {port}")


@task
def test(ctx, coverage=False):
    """Run tests"""
    set_django_env()
    if coverage:
        ctx.run("pytest --cov=internal --cov-report=html")
    else:
        ctx.run("pytest")


@task
def test_verbose(ctx):
    """Run tests with verbose output"""
    set_django_env()
    ctx.run("pytest -v")


@task
def format(ctx):
    """Format code using black"""
    print("Formatting code...")
    ctx.run("black .")


@task
def lint(ctx):
    """Run linting checks"""
    print("Running linting checks...")
    ctx.run("flake8 .")


@task
def clean(ctx):
    """Clean up Python cache files"""
    print("Cleaning cache files...")
    ctx.run("find . -type d -name __pycache__ -exec rm -r {} +")
    ctx.run("find . -type f -name '*.pyc' -delete")
    ctx.run("find . -type f -name '*.pyo' -delete")
    ctx.run("find . -type f -name '*.pyd' -delete")


@task
def reset_db(ctx):
    """Reset the database"""
    print("Resetting database...")
    if os.path.exists("words.db"):
        os.remove("words.db")
    ctx.run("python scripts/manage.py migrate")


@task
def generate_docs(ctx):
    """Generate API documentation"""
    print("Generating API documentation...")
    ctx.run("python scripts/manage.py generate_schema --file openapi-schema.yml")
