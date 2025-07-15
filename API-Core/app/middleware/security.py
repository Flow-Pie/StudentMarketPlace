from flask import request


class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
        self.setup_headers()

    def setup_headers(self):
        @self.app.after_request
        def add_security_headers(response):
            # Base security headers
            headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Referrer-Policy': 'strict-origin-when-cross-origin',
            }

            # Special CSP for Swagger UI
            if request.path == '/':
                csp = "default-src 'self'; " \
                      "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; " \
                      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; " \
                      "img-src 'self' data: https://cdn.jsdelivr.net; " \
                      "font-src 'self' https://cdn.jsdelivr.net; " \
                      "connect-src 'self'"
                headers['Content-Security-Policy'] = csp
            else:
                # Stricter CSP for other routes
                headers['Content-Security-Policy'] = "default-src 'self';"

            # Add headers to response
            for header, value in headers.items():
                response.headers[header] = value

            return response
