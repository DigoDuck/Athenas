from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def me(request):
    """Who is signed in. Also sets the CSRF cookie the screens send back on every write."""
    if not request.user.is_authenticated:
        return Response({"detail": "Entre para continuar."}, status=403)
    return Response({"username": request.user.get_username()})


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    # DRF only checks CSRF for a signed-in session; a login form needs it too (login CSRF).
    SessionAuthentication().enforce_csrf(request)
    user = authenticate(
        request._request,
        username=str(request.data.get("username", "")),
        password=str(request.data.get("password", "")),
    )
    if user is None:
        return Response({"detail": "Usuário ou senha incorretos."}, status=400)
    login(request._request, user)
    return Response({"username": user.get_username()})


@api_view(["POST"])
def logout_view(request):
    logout(request._request)
    return Response(status=204)
