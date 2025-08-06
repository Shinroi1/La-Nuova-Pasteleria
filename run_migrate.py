# run_migrate.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
django.setup()

from django.core.management import call_command

call_command('makemigrations', 'myapp')  # 👈 Explicitly name your app
call_command('migrate')
