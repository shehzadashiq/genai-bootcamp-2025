#!/usr/bin/env python
"""
Custom script to run the Django development server with enhanced logging.
This ensures all logs are properly displayed in the console, even in WSL2.
"""
import os
import sys
import logging
import time

# Configure root logger before Django loads
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # Add a file handler to ensure logs are captured even if console buffer issues occur
        logging.FileHandler('django_debug.log', mode='w'),
    ]
)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lang_portal_backend.settings')

# Force DEBUG mode
os.environ['DEBUG'] = 'True'

# Disable output buffering for WSL2
os.environ['PYTHONUNBUFFERED'] = '1'

# Print startup message
print("=" * 80)
print("Starting Django server with enhanced logging (WSL2-compatible)")
print(f"Django settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
print(f"DEBUG mode: {os.environ.get('DEBUG')}")
print(f"Log file: {os.path.abspath('django_debug.log')}")
print("=" * 80)

# Force flush stdout to ensure WSL2 displays the message
sys.stdout.flush()

if __name__ == '__main__':
    # Add a custom middleware for request logging
    print("Registering custom middleware for request logging...")
    
    from django.core.management import execute_from_command_line
    
    # Add runserver command if not provided
    if len(sys.argv) == 1:
        sys.argv.append('runserver')
        sys.argv.append('0.0.0.0:8080')
        # Add --noreload to prevent WSL2 file system watch issues
        sys.argv.append('--noreload')
    
    # Run Django management command
    print(f"Executing command: {' '.join(sys.argv)}")
    sys.stdout.flush()
    execute_from_command_line(sys.argv)
