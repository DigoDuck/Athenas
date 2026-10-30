import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Create the superuser named in DJANGO_SUPERUSER_USERNAME, with DJANGO_SUPERUSER_PASSWORD, "
        "unless it exists. Runs on every start; an existing account is never changed."
    )

    def handle(self, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "")
        if not username:
            return
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            return
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        if not password:
            raise CommandError("DJANGO_SUPERUSER_PASSWORD is empty.")
        User.objects.create_superuser(username, password=password)
        self.stdout.write(f"Superuser {username} created.")
