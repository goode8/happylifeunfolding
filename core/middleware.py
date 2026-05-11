from django.http import HttpResponseForbidden

BLOCKED_IPS = {
    '3.64.223.136',
}


class BlockIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR')
        if ip in BLOCKED_IPS:
            return HttpResponseForbidden()
        return self.get_response(request)
