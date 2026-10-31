import pytest
from django.test import Client


@pytest.fixture
def client(db, django_user_model):
    """pytest-django's client, signed in: all but health and auth need a login (D-044)."""
    signed_in = Client()
    signed_in.force_login(django_user_model.objects.create_user("estudante"))
    return signed_in
