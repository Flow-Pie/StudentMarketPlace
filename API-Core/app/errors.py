# API-Core/app/errors.py
import logging
import platform
from pathlib import Path
from flask import jsonify
from werkzeug.exceptions import HTTPException
from logging.handlers import RotatingFileHandler


class APIError(Exception):
    """Base API Error Class"""

    def __init__(self, message, code, status_code=500):
        super().__init__()
        self.message = message
        self.code = code
        self.status_code = status_code


class ValidationError(APIError):
    """Validation Error (400-level)"""

    def __init__(self, message, code="VALIDATION_ERROR"):
        super().__init__(message, code, 400)


def configure_logging(app):
    # Determine log directory based on environment
    if platform.system() == 'Linux':
        log_dir = Path('/var/log/student-marketplace/')
    elif platform.system() == 'Windows':
        log_dir = Path('C:\\student-marketplace\\logs\\')
    else:
        log_dir = Path('./logs/')

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'app-errors.log'

    # Configure rotating file handler
    handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024 * 10,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )

    class RedactingFilter(logging.Filter):
        def filter(self, record):
            sensitive_keys = ['password', 'token', 'authorization']
            for key in sensitive_keys:
                if key in record.msg.lower():
                    record.msg = record.msg.replace(key, '***')
            return True

    handler.addFilter(RedactingFilter())
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.ERROR)


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Convert APIError instances to proper JSON responses"""
        app.logger.error(f"API Error [{error.code}]: {error.message}")

        response = jsonify({
            'error': error.code,
            'message': error.message,
            'status': error.status_code
        })
        response.status_code = error.status_code
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        app.logger.error(f"HTTP Error {e.code}: {e.description}")
        return jsonify({
            'error': True,
            'message': e.description,
            'code': e.name.replace(' ', '_').upper()
        }), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        app.logger.exception("Unhandled exception occurred")
        return jsonify({
            'error': True,
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_SERVER_ERROR'
        }), 500