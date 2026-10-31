from django.contrib import admin
from django.contrib.staticfiles.views import serve
from django.db import connection
from django.urls import include, path, re_path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from config import auth


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return Response({"status": "ok"})


urlpatterns = [
    path("api/health/", health),
    path("api/auth/me/", auth.me),
    path("api/auth/login/", auth.login_view),
    path("api/auth/logout/", auth.logout_view),
    path("admin/", admin.site.urls),
    # shortcut: Django serves the admin's own CSS and JS; fine for one admin, move to nginx if
    # the app ever ships static files of its own.
    re_path(r"^static/(?P<path>.*)$", serve, {"insecure": True}),
    path("api/", include("organization.urls")),
    path("api/", include("content.urls")),
    path("api/", include("activity.urls")),
]
