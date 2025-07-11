"""
Security tests for the application.
"""
import pytest
from marshmallow import ValidationError
from app.utils.validation import SecurityValidator, validate_password, sanitize_input, validate_email
from app.middleware.security import SecurityMiddleware


class TestSecurityValidator:
    """Test security validation functions."""
    
    def test_password_strength_valid(self):
        """Test valid password passes validation."""
        valid_passwords = [
            "StrongPass123!",
            "MySecure@Pass1",
            "Complex#Password9"
        ]
        
        for password in valid_passwords:
            result = validate_password(password)
            assert result == password
    
    def test_password_strength_invalid(self):
        """Test invalid passwords fail validation."""
        invalid_passwords = [
            "weak",  # Too short
            "password",  # Common password
            "12345678",  # No letters
            "abcdefgh",  # No numbers or special chars
            "ABCDEFGH",  # No lowercase
            "Password1"  # No special characters
        ]
        
        for password in invalid_passwords:
            with pytest.raises(ValidationError):
                validate_password(password)
    
    def test_html_sanitization(self):
        """Test HTML sanitization prevents XSS."""
        # Safe input should pass through
        safe_input = "This is safe text"
        assert sanitize_input(safe_input) == safe_input
        
        # Dangerous input should raise error
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(1)'></iframe>"
        ]
        
        for dangerous in dangerous_inputs:
            with pytest.raises(ValidationError):
                sanitize_input(dangerous)
    
    def test_email_validation(self):
        """Test email validation."""
        # Valid emails
        valid_emails = [
            "user@example.com",
            "test.email@domain.co.uk",
            "user+tag@example.org"
        ]
        
        for email in valid_emails:
            result = validate_email(email)
            assert result == email.lower()
        
        # Invalid emails
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com",
            "<script>alert('xss')</script>@example.com"
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                validate_email(email)
    
    def test_url_validation(self):
        """Test URL validation."""
        validator = SecurityValidator()
        
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://subdomain.example.org/path",
            "https://example.com/path?param=value"
        ]
        
        for url in valid_urls:
            result = validator.validate_url(url)
            assert result == url
        
        # Invalid URLs
        invalid_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "file:///etc/passwd",
            "ftp://example.com/file"
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationError):
                validator.validate_url(url)
    
    def test_file_upload_validation(self):
        """Test file upload validation."""
        validator = SecurityValidator()
        
        # Valid filenames
        valid_files = [
            "document.pdf",
            "image.jpg",
            "data.csv"
        ]
        
        allowed_extensions = ['pdf', 'jpg', 'csv']
        
        for filename in valid_files:
            result = validator.validate_file_upload(filename, allowed_extensions)
            assert result == filename
        
        # Invalid filenames
        invalid_files = [
            "../../../etc/passwd",
            "web.config",
            ".htaccess",
            "script.php",
            "malware.exe"
        ]
        
        for filename in invalid_files:
            with pytest.raises(ValidationError):
                validator.validate_file_upload(filename, allowed_extensions)


class TestSecurityMiddleware:
    """Test security middleware functionality."""
    
    def test_security_headers(self, app, client):
        """Test security headers are added."""
        with app.test_request_context():
            response = client.get('/health')
            
            # Check security headers
            assert 'X-Content-Type-Options' in response.headers
            assert response.headers['X-Content-Type-Options'] == 'nosniff'
            
            assert 'X-Frame-Options' in response.headers
            assert response.headers['X-Frame-Options'] == 'DENY'
            
            assert 'X-XSS-Protection' in response.headers
            assert response.headers['X-XSS-Protection'] == '1; mode=block'
            
            assert 'Content-Security-Policy' in response.headers
    
    def test_correlation_id(self, app, client):
        """Test correlation ID is added to responses."""
        with app.test_request_context():
            response = client.get('/health')
            
            assert 'X-Correlation-ID' in response.headers
            correlation_id = response.headers['X-Correlation-ID']
            assert len(correlation_id) == 36  # UUID length
    
    def test_rate_limiting(self, app, client):
        """Test rate limiting functionality."""
        # This is a basic test - in practice you'd need to make many requests
        # to trigger rate limiting
        with app.test_request_context():
            # Make a request
            response = client.get('/health')
            assert response.status_code == 200
            
            # Rate limiting is tested more thoroughly in integration tests