from django.http import JsonResponse


class JsonWritesOnly:
    """Writes must be JSON (DECISIONS.md D-039).

    With no login and no CSRF cookie, any page open in the same browser could post a form to
    127.0.0.1 and write history. A form or plain text needs no CORS preflight; JSON does, and this
    API never answers one, so a page on another site cannot send it.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view, args, kwargs):
        # After URL resolution, so an unknown route still answers 404.
        writes = request.method in ("POST", "PUT", "PATCH")
        if writes and request.content_type != "application/json":
            return JsonResponse({"detail": "Envie o corpo como JSON."}, status=415)
        return None
