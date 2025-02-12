import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Set up Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()
