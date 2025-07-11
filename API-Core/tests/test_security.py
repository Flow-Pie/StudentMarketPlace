"""Security-focused tests for the application."""

import pytest
from flask import url_for
from app.utils.validation import EnhancedValidator


class TestSecurityHeaders:
    """Test security headers implementation."""
    
    def test_security_headers_present(self, client):
        """Test that security headers are present in responses."""
        response = client.get('/health')
        
        # Check for security headers
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
        
        assert 'X-XSS-Protection' in response.headers
        assert response.headers['X-XSS-Protection'] == '1; mode=block'
        
        assert 'Content-Security-Policy' in response.headers
    
    def test_correlation_id_header(self, client):
        """Test that correlation ID is added to responses."""
        response = client.get('/health')
        assert 'X-Correlation-ID' in response.headers
        assert len(response.headers['X-Correlation-ID']) > 0


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_html_sanitization(self):
        """Test HTML sanitization."""
        # Test script tag removal
        malicious_input = "<script>alert('xss')</script>Hello"
        with pytest.raises(Exception):  # Should raise ValidationError
            EnhancedValidator.sanitize_html(malicious_input)
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Weak password
        weak_result = EnhancedValidator.validate_password_strength("123")
        assert not weak_result['valid']
        assert weak_result['strength'] == 'weak'
        
        # Strong password
        strong_result = EnhancedValidator.validate_password_strength("MyStr0ng!Pass")
        assert strong_result['valid']
        assert strong_result['strength'] in ['medium', 'strong']
    
    def test_url_validation(self):
        """Test URL validation."""
        # Valid URLs
        assert EnhancedValidator.validate_url("https://example.com")
        assert EnhancedValidator.validate_url("http://test.org")
        
        # Invalid URLs
        assert not EnhancedValidator.validate_url("javascript:alert('xss')")
        assert not EnhancedValidator.validate_url("data:text/html,<script>alert('xss')</script>")


class TestAPIKeyAuthentication:
    """Test API key authentication."""
    
    def test_missing_api_key(self, client):
        """Test request without API key to protected endpoint."""
        # This would test an endpoint that requires API key
        # Implementation depends on which endpoints use the decorator
        pass
    
    def test_invalid_api_key(self, client):
        """Test request with invalid API key."""
        headers = {'X-API-Key': 'invalid-key'}
        # Test against protected endpoint
        pass


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_enforcement(self, client):
        """Test that rate limiting is enforced."""
        # Make multiple requests to test rate limiting
        # This depends on the rate limiting configuration
        pass


class TestDataValidation:
    """Test data validation in API endpoints."""
    
    def test_item_creation_validation(self, client, auth_headers):
        """Test item creation with invalid data."""
        # Test with missing required fields
        response = client.post('/api/items', 
                              json={}, 
                              headers=auth_headers)
        assert response.status_code == 400
        
        # Test with invalid price
        response = client.post('/api/items',
                              json={
                                  'title': 'Test Item',
                                  'description': 'Test description',
                                  'price': -10,  # Invalid negative price
                                  'category': 'BOOKS'
                              },
                              headers=auth_headers)
        assert response.status_code == 400
    
    def test_xss_prevention_in_item_data(self, client, auth_headers):
        """Test XSS prevention in item creation."""
        malicious_data = {
            'title': '<script>alert("xss")</script>Malicious Item',
            'description': 'Normal description',
            'price': 10.00,
            'category': 'BOOKS'
        }
        
        response = client.post('/api/items',
                              json=malicious_data,
                              headers=auth_headers)
        
        # Should either reject the request or sanitize the input
        if response.status_code == 201:
            # If accepted, check that script tags are removed
            assert '<script>' not in response.json.get('data', {}).get('title', '')