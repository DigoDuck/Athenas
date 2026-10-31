import json

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db

PASSWORD = "senha-sintetica-longa"


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user("ana", password=PASSWORD)


def post_json(client, url, body, **headers):
    return client.post(url, json.dumps(body), content_type="application/json", **headers)


def sign_in(browser, token, password=PASSWORD):
    body = {"username": "ana", "password": password}
    return post_json(browser, "/api/auth/login/", body, HTTP_X_CSRFTOKEN=token)


def csrf_client():
    """A browser: CSRF enforced, token read from the cookie that /api/auth/me/ sets."""
    browser = Client(enforce_csrf_checks=True)
    browser.get("/api/auth/me/")
    return browser, browser.cookies["csrftoken"].value


def test_anonymous_requests_are_refused():
    anonymous = Client()
    assert anonymous.get("/api/areas/").status_code == 403
    assert post_json(anonymous, "/api/areas/", {"name": "Direito"}).status_code == 403
    assert anonymous.get("/api/auth/me/").status_code == 403


def test_health_stays_open_for_the_host_check():
    assert Client().get("/api/health/").status_code == 200


def test_login_opens_the_api_and_logout_closes_it(user):
    browser, token = csrf_client()
    response = sign_in(browser, token)
    assert response.status_code == 200
    assert response.json() == {"username": "ana"}
    assert browser.get("/api/auth/me/").json() == {"username": "ana"}
    assert browser.get("/api/areas/").status_code == 200

    token = browser.cookies["csrftoken"].value  # login rotates the token
    assert post_json(browser, "/api/auth/logout/", {}, HTTP_X_CSRFTOKEN=token).status_code == 204
    assert browser.get("/api/areas/").status_code == 403


def test_wrong_password_is_refused_with_a_message(user):
    browser, token = csrf_client()
    response = sign_in(browser, token, password="errada")
    assert response.status_code == 400
    assert response.json()["detail"] == "Usuário ou senha incorretos."
    assert browser.get("/api/areas/").status_code == 403


def test_login_and_writes_need_the_csrf_token(user):
    browser, token = csrf_client()
    no_token = post_json(browser, "/api/auth/login/", {"username": "ana", "password": PASSWORD})
    assert no_token.status_code == 403

    sign_in(browser, token)
    area = {"name": "Direito"}
    assert post_json(browser, "/api/areas/", area).status_code == 403
    token = browser.cookies["csrftoken"].value
    assert post_json(browser, "/api/areas/", area, HTTP_X_CSRFTOKEN=token).status_code == 201


def test_admin_login_page_is_not_blocked_by_the_json_rule():
    browser = Client(enforce_csrf_checks=True)
    page = browser.get("/admin/login/")
    assert page.status_code == 200
    token = browser.cookies["csrftoken"].value
    form = {"username": "x", "password": "y", "csrfmiddlewaretoken": token}
    response = browser.post("/admin/login/", form)
    assert response.status_code == 200  # the form again, with its error; not 415


def test_ensure_superuser_creates_once_and_never_changes_it(monkeypatch, django_user_model):
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "diogo")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", PASSWORD)
    call_command("ensure_superuser")
    call_command("ensure_superuser")
    admin = django_user_model.objects.get(username="diogo")
    assert admin.is_superuser and admin.check_password(PASSWORD)

    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "outra-senha-sintetica")
    call_command("ensure_superuser")
    admin.refresh_from_db()
    assert admin.check_password(PASSWORD)


def test_ensure_superuser_does_nothing_without_a_username(monkeypatch, django_user_model):
    monkeypatch.delenv("DJANGO_SUPERUSER_USERNAME", raising=False)
    call_command("ensure_superuser")
    assert not django_user_model.objects.exists()
