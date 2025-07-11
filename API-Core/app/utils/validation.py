"""Enhanced validation utilities."""

import re
from typing import Any, Dict, List, Optional
from marshmallow import ValidationError
import bleach
from urllib.parse import urlparse


class EnhancedValidator:
    """Enhanced validation utilities for security and data integrity."""
    
    # Allowed HTML tags for rich text (if needed)
    ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    ALLOWED_ATTRIBUTES = {}
    
    # Common dangerous patterns
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
    ]
    
    @classmethod
    def sanitize_html(cls, value: str, allow_tags: bool = False) -> str:
        """Sanitize HTML content."""
        if not value:
            return value
        
        if allow_tags:
            # Allow specific tags
            cleaned = bleach.clean(
                value, 
                tags=cls.ALLOWED_TAGS,
                attributes=cls.ALLOWED_ATTRIBUTES,
                strip=True
            )
        else:
            # Strip all HTML
            cleaned = bleach.clean(value, tags=[], attributes={}, strip=True)
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                raise ValidationError("Content contains potentially dangerous code")
        
        return cleaned
    
    @classmethod
    def validate_email_domain(cls, email: str, allowed_domains: Optional[List[str]] = None) -> bool:
        """Validate email domain against whitelist."""
        if not allowed_domains:
            return True
        
        domain = email.split('@')[1].lower()
        return domain in [d.lower() for d in allowed_domains]
    
    @classmethod
    def validate_password_strength(cls, password: str) -> Dict[str, Any]:
        """Comprehensive password strength validation."""
        issues = []
        score = 0
        
        # Length check
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        elif len(password) >= 12:
            score += 2
        else:
            score += 1
        
        # Character variety checks
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain lowercase letters")
        else:
            score += 1
        
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain uppercase letters")
        else:
            score += 1
        
        if not re.search(r'\d', password):
            issues.append("Password must contain numbers")
        else:
            score += 1
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain special characters")
        else:
            score += 1
        
        # Common password patterns
        common_patterns = [
            r'123456',
            r'password',
            r'qwerty',
            r'abc123'
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                issues.append("Password contains common patterns")
                score -= 1
                break
        
        # Determine strength
        if score >= 6:
            strength = "strong"
        elif score >= 4:
            strength = "medium"
        else:
            strength = "weak"
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'strength': strength,
            'score': max(0, score)
        }
    
    @classmethod
    def validate_url(cls, url: str, allowed_schemes: List[str] = None) -> bool:
        """Validate URL format and scheme."""
        if not allowed_schemes:
            allowed_schemes = ['http', 'https']
        
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in allowed_schemes and
                parsed.netloc and
                not any(dangerous in url.lower() for dangerous in ['javascript:', 'data:', 'vbscript:'])
            )
        except Exception:
            return False
    
    @classmethod
    def validate_file_upload(cls, filename: str, content_type: str, 
                           allowed_extensions: List[str], 
                           allowed_mime_types: List[str]) -> Dict[str, Any]:
        """Comprehensive file upload validation."""
        issues = []
        
        # Extension check
        if '.' not in filename:
            issues.append("File must have an extension")
        else:
            ext = filename.rsplit('.', 1)[1].lower()
            if ext not in allowed_extensions:
                issues.append(f"File extension '{ext}' not allowed")
        
        # MIME type check
        if content_type not in allowed_mime_types:
            issues.append(f"File type '{content_type}' not allowed")
        
        # Filename security check
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        if any(char in filename for char in dangerous_chars):
            issues.append("Filename contains dangerous characters")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }


def validate_json_schema(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """Validate JSON data against required fields."""
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    return {
        'valid': len(missing_fields) == 0,
        'missing_fields': missing_fields
    }