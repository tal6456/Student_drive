"""
Django management and control utility
=====================================

What is this file for?
----------------------
This file is the site's command-line interface (CLI). It acts as the bridge
between you and the Django infrastructure, allowing maintenance, development,
and management tasks to run.

It supports the following actions:
1. Run the site: start the local development server (`runserver`) to test it.
2. Manage the database: create tables (`makemigrations`) and update them
   (`migrate`) according to model changes.
3. Create users: create superusers (`createsuperuser`) for site management.
4. Run custom commands: execute custom scripts built for Student Drive,
   for cleanup jobs and other tasks.
5. Testing: run automated checks to verify the code is working correctly.

Important: this file automatically loads the project's settings module,
so it always knows which database to connect to and how to boot the app.
"""

#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_drive.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
