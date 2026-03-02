from django.conf import settings
from django.http import HttpResponse
from django.middleware.csrf import get_token


class EnsureCSRFCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ensure CSRF cookie is always available for AJAX POST actions.
        get_token(request)
        return self.get_response(request)


class CORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get('Origin')
        if request.method == 'OPTIONS' and origin and request.headers.get('Access-Control-Request-Method'):
            response = HttpResponse(status=204)
            return self._apply_cors_headers(response, origin)

        response = self.get_response(request)
        if origin:
            response = self._apply_cors_headers(response, origin)
        return response

    def _apply_cors_headers(self, response, origin):
        allowed_origins = set(getattr(settings, 'CORS_ALLOWED_ORIGINS', []))
        if origin not in allowed_origins:
            return response

        response['Access-Control-Allow-Origin'] = origin
        if getattr(settings, 'CORS_ALLOW_CREDENTIALS', False):
            response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Methods'] = ', '.join(
            getattr(settings, 'CORS_ALLOW_METHODS', ['GET', 'POST', 'OPTIONS'])
        )
        response['Access-Control-Allow-Headers'] = ', '.join(
            getattr(settings, 'CORS_ALLOW_HEADERS', ['Content-Type'])
        )
        current_vary = response.get('Vary')
        if current_vary:
            if 'Origin' not in [item.strip() for item in current_vary.split(',')]:
                response['Vary'] = f'{current_vary}, Origin'
        else:
            response['Vary'] = 'Origin'
        return response


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        policy = getattr(settings, 'CONTENT_SECURITY_POLICY', None)
        if not policy:
            return response

        header_name = (
            'Content-Security-Policy-Report-Only'
            if getattr(settings, 'CSP_REPORT_ONLY', False)
            else 'Content-Security-Policy'
        )
        response[header_name] = self._build_policy(policy)
        return response

    @staticmethod
    def _build_policy(policy):
        directives = []
        for directive, values in policy.items():
            if values:
                directives.append(f"{directive} {' '.join(values)}")
            else:
                directives.append(directive)
        return '; '.join(directives)
