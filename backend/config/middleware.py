from django.http import JsonResponse


class JsonWritesOnly:
    """API writes must be JSON (DECISIONS.md D-039).

    Kept after login (D-044) as a second guard next to CSRF: a form or plain text needs no CORS
    preflight; JSON does, and this API never answers one, so a page on another site cannot send
    it. The admin posts forms and has Django's CSRF check instead.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view, args, kwargs):
        # After URL resolution, so an unknown route still answers 404.
        if request.path.startswith("/admin/"):
            return None
        writes = request.method in ("POST", "PUT", "PATCH")
        if writes and request.content_type != "application/json":
            return JsonResponse({"detail": "Envie o corpo como JSON."}, status=415)
        return None
