"""
Security middleware for enhanced application security.
"""
import logging
import uuid
from functools import wraps
from flask import request, g, current_app, abort, jsonify
from werkzeug.exceptions import TooManyRequests
import time
import hashlib

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Enhanced security middleware with comprehensive protection."""
    
    def __init__(self, app=None):
        self.app = app
        self.rate_limit_storage = {}
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware with Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Configure security settings
        app.config.setdefault('SECURITY_HEADERS_ENABLED', True)
        app.config.setdefault('RATE_LIMIT_ENABLED', True)
        app.config.setdefault('CORRELATION_ID_ENABLED', True)
    
    def before_request(self):
        """Execute before each request."""
        # Add correlation ID
        if current_app.config.get('CORRELATION_ID_ENABLED', True):
            g.correlation_id = str(uuid.uuid4())
        
        # Rate limiting
        if current_app.config.get('RATE_LIMIT_ENABLED', True):
            self._check_rate_limit()
        
        # Log request
        logger.info(
            "Request started",
            extra={
                'correlation_id': getattr(g, 'correlation_id', None),
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr
            }
        )
    
    def after_request(self, response):
        """Execute after each request."""
        # Add security headers
        if current_app.config.get('SECURITY_HEADERS_ENABLED', True):
            self._add_security_headers(response)
        
        # Add correlation ID to response
        if hasattr(g, 'correlation_id'):
            response.headers['X-Correlation-ID'] = g.correlation_id
        
        return response
    
    def _add_security_headers(self, response):
        """Add comprehensive security headers."""
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HTTPS enforcement (if enabled)
        if current_app.config.get('FORCE_HTTPS', False):
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )
    
    def _check_rate_limit(self):
        """Simple rate limiting implementation."""
        client_id = self._get_client_id()
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_rate_limit_storage(current_time)
        
        # Check rate limit
        if client_id in self.rate_limit_storage:
            requests = self.rate_limit_storage[client_id]
            # Allow 100 requests per minute
            if len(requests) >= 100:
                raise TooManyRequests("Rate limit exceeded")
        
        # Add current request
        if client_id not in self.rate_limit_storage:
            self.rate_limit_storage[client_id] = []
        
        self.rate_limit_storage[client_id].append(current_time)
    
    def _get_client_id(self):
        """Get client identifier for rate limiting."""
        # Use IP address as client identifier
        return hashlib.md5(
            (request.remote_addr or 'unknown').encode()
        ).hexdigest()
    
    def _cleanup_rate_limit_storage(self, current_time):
        """Clean up old rate limit entries."""
        cutoff_time = current_time - 60  # 1 minute window
        
        for client_id in list(self.rate_limit_storage.keys()):
            self.rate_limit_storage[client_id] = [
                req_time for req_time in self.rate_limit_storage[client_id]
                if req_time > cutoff_time
            ]
            
            if not self.rate_limit_storage[client_id]:
                del self.rate_limit_storage[client_id]


def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key (implement your validation logic)
        if not _validate_api_key(api_key):
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def _validate_api_key(api_key):
    """Validate API key (implement your validation logic)."""
    # This is a placeholder - implement actual validation
    valid_keys = current_app.config.get('VALID_API_KEYS', [])
    return api_key in valid_keys