"""Security middleware for enhanced protection."""

from flask import request, g
import uuid
from functools import wraps


class SecurityMiddleware:
    """Enhanced security middleware for the application."""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware with Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Configure security settings
        app.config.setdefault('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)  # 16MB
        app.config.setdefault('FORCE_HTTPS', True)
    
    def before_request(self):
        """Process request before handling."""
        # Add correlation ID for request tracing
        g.correlation_id = str(uuid.uuid4())
        
        # Enforce HTTPS in production
        if (self.app.config.get('FORCE_HTTPS') and 
            not request.is_secure and 
            self.app.config.get('ENV') == 'production'):
            return {'error': 'HTTPS required'}, 400
    
    def after_request(self, response):
        """Add security headers to response."""
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS header for HTTPS
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # Add correlation ID to response headers for debugging
        response.headers['X-Correlation-ID'] = getattr(g, 'correlation_id', 'unknown')
        
        return response


def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return {'error': 'API key required', 'code': 'API_KEY_MISSING'}, 401
        
        # In production, validate against stored API keys
        # For now, we'll use a simple check
        valid_keys = ['dev-key-123', 'admin-key-456']  # Move to environment variables
        if api_key not in valid_keys:
            return {'error': 'Invalid API key', 'code': 'API_KEY_INVALID'}, 401
        
        return f(*args, **kwargs)
    return decorated_function