"""
Enhanced validation utilities for security and data integrity.
"""
import re
import bleach
import urllib.parse
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Security-focused validation utilities."""
    
    # Password strength requirements
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_PATTERNS = {
        'uppercase': r'[A-Z]',
        'lowercase': r'[a-z]',
        'digit': r'\d',
        'special': r'[!@#$%^&*(),.?":{}|<>]'
    }
    
    # XSS prevention
    ALLOWED_HTML_TAGS = []  # No HTML tags allowed by default
    ALLOWED_HTML_ATTRIBUTES = {}
    
    # URL validation
    ALLOWED_URL_SCHEMES = ['http', 'https']
    
    @classmethod
    def validate_password_strength(cls, password):
        """Validate password strength requirements."""
        errors = []
        
        if len(password) < cls.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {cls.PASSWORD_MIN_LENGTH} characters long")
        
        for requirement, pattern in cls.PASSWORD_PATTERNS.items():
            if not re.search(pattern, password):
                errors.append(f"Password must contain at least one {requirement} character")
        
        # Check for common weak passwords
        weak_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
        if password.lower() in weak_passwords:
            errors.append("Password is too common and easily guessable")
        
        if errors:
            raise ValidationError(errors)
        
        return password
    
    @classmethod
    def sanitize_html(cls, value):
        """Sanitize HTML content to prevent XSS attacks."""
        if not value:
            return value
        
        # Clean HTML using bleach
        cleaned = bleach.clean(
            value,
            tags=cls.ALLOWED_HTML_TAGS,
            attributes=cls.ALLOWED_HTML_ATTRIBUTES,
            strip=True
        )
        
        # Check if content was modified (potential XSS attempt)
        if cleaned != value:
            logger.warning(
                "Potential XSS attempt detected",
                extra={'original': value, 'cleaned': cleaned}
            )
            raise ValidationError("HTML tags or unsafe characters detected")
        
        return cleaned
    
    @classmethod
    def validate_url(cls, url):
        """Validate URL for security."""
        if not url:
            return url
        
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Check scheme
            if parsed.scheme not in cls.ALLOWED_URL_SCHEMES:
                raise ValidationError(f"URL scheme must be one of: {', '.join(cls.ALLOWED_URL_SCHEMES)}")
            
            # Check for suspicious patterns
            suspicious_patterns = [
                'javascript:',
                'data:',
                'vbscript:',
                'file:',
                'ftp:'
            ]
            
            url_lower = url.lower()
            for pattern in suspicious_patterns:
                if pattern in url_lower:
                    raise ValidationError("URL contains suspicious content")
            
            return url
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError("Invalid URL format")
    
    @classmethod
    def validate_file_upload(cls, filename, allowed_extensions=None, max_size=None):
        """Validate file upload for security."""
        if not filename:
            raise ValidationError("Filename is required")
        
        # Check file extension
        if allowed_extensions:
            file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if file_ext not in [ext.lower() for ext in allowed_extensions]:
                raise ValidationError(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
        
        # Check for suspicious filenames
        suspicious_patterns = [
            '../',
            '..\\',
            '/etc/',
            '/var/',
            '/usr/',
            'web.config',
            '.htaccess',
            '.php',
            '.jsp',
            '.asp'
        ]
        
        filename_lower = filename.lower()
        for pattern in suspicious_patterns:
            if pattern in filename_lower:
                raise ValidationError("Filename contains suspicious content")
        
        return filename
    
    @classmethod
    def validate_email_format(cls, email):
        """Enhanced email validation."""
        if not email:
            raise ValidationError("Email is required")
        
        # Basic email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            'javascript:',
            '<script',
            'onclick=',
            'onerror='
        ]
        
        email_lower = email.lower()
        for pattern in suspicious_patterns:
            if pattern in email_lower:
                raise ValidationError("Email contains suspicious content")
        
        return email.lower()
    
    @classmethod
    def validate_phone_number(cls, phone):
        """Validate phone number format."""
        if not phone:
            return phone
        
        # Remove common formatting characters
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        
        # Basic phone number validation (international format)
        phone_pattern = r'^\+?[1-9]\d{1,14}$'
        
        if not re.match(phone_pattern, cleaned_phone):
            raise ValidationError("Invalid phone number format")
        
        return cleaned_phone
    
    @classmethod
    def validate_numeric_range(cls, value, min_val=None, max_val=None):
        """Validate numeric value within range."""
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError("Value must be a number")
        
        if min_val is not None and num_value < min_val:
            raise ValidationError(f"Value must be at least {min_val}")
        
        if max_val is not None and num_value > max_val:
            raise ValidationError(f"Value must be at most {max_val}")
        
        return num_value
    
    @classmethod
    def validate_text_length(cls, text, min_length=None, max_length=None):
        """Validate text length constraints."""
        if not text:
            text = ""
        
        text_length = len(text)
        
        if min_length is not None and text_length < min_length:
            raise ValidationError(f"Text must be at least {min_length} characters long")
        
        if max_length is not None and text_length > max_length:
            raise ValidationError(f"Text must be at most {max_length} characters long")
        
        return text


# Convenience functions for common validations
def validate_password(password):
    """Validate password strength."""
    return SecurityValidator.validate_password_strength(password)

def sanitize_input(value):
    """Sanitize user input."""
    return SecurityValidator.sanitize_html(value)

def validate_url(url):
    """Validate URL."""
    return SecurityValidator.validate_url(url)

def validate_email(email):
    """Validate email."""
    return SecurityValidator.validate_email_format(email)

def validate_file(filename, allowed_extensions=None):
    """Validate file upload."""
    return SecurityValidator.validate_file_upload(filename, allowed_extensions)