# Security Guide

This document outlines the security measures implemented in the StudentMarketPlace application and provides guidelines for maintaining security.

## 🔒 Security Features

### Authentication & Authorization
- **JWT-based authentication** with secure token management
- **Role-based access control (RBAC)** for admin functions
- **Token revocation** system for logout functionality
- **Password strength requirements** with validation
- **Account lockout** after failed login attempts

### Input Validation & Sanitization
- **HTML sanitization** to prevent XSS attacks
- **SQL injection prevention** through ORM usage
- **File upload validation** with type and size restrictions
- **URL validation** to prevent malicious redirects
- **JSON schema validation** for API requests

### Security Headers
- **Content Security Policy (CSP)** to prevent XSS
- **X-Frame-Options** to prevent clickjacking
- **X-Content-Type-Options** to prevent MIME sniffing
- **X-XSS-Protection** for legacy browser protection
- **Strict-Transport-Security (HSTS)** for HTTPS enforcement

### Rate Limiting
- **API rate limiting** to prevent abuse
- **Login attempt limiting** to prevent brute force attacks
- **Request size limits** to prevent DoS attacks

## 🛡️ Security Best Practices

### For Developers

#### 1. Input Validation
Always validate and sanitize user input:

```python
from app.utils.validation import EnhancedValidator

# Sanitize HTML content
clean_content = EnhancedValidator.sanitize_html(user_input)

# Validate password strength
password_check = EnhancedValidator.validate_password_strength(password)
if not password_check['valid']:
    raise ValidationError(password_check['issues'])
```

#### 2. Database Queries
Use parameterized queries and ORM methods:

```python
# Good - Using ORM
user = User.query.filter_by(email=email).first()

# Bad - String concatenation (vulnerable to SQL injection)
# query = f"SELECT * FROM users WHERE email = '{email}'"
```

#### 3. Error Handling
Don't expose sensitive information in error messages:

```python
# Good
return {'error': 'Authentication failed'}, 401

# Bad - exposes user existence
# return {'error': 'User john@example.com not found'}, 404
```

#### 4. Logging
Use the security-aware logging system:

```python
from flask import current_app

# Logs will automatically redact sensitive information
current_app.logger.info(f"User login attempt", extra={
    'user_id': user.id,
    'ip_address': request.remote_addr
})
```

### For Deployment

#### 1. Environment Variables
Never commit sensitive data to version control:

```bash
# Use environment variables for secrets
JWT_SECRET_KEY=your-secure-secret-here
DATABASE_URL=postgresql://user:pass@host:port/db
API_KEYS=key1,key2,key3
```

#### 2. HTTPS Configuration
Always use HTTPS in production:

```python
# Set in production environment
FORCE_HTTPS=true
```

#### 3. Database Security
- Use strong database passwords
- Limit database user permissions
- Enable database encryption at rest
- Use connection pooling with limits

#### 4. Container Security
```dockerfile
# Use non-root user in containers
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Keep base images updated
FROM python:3.11-slim
```

## 🔍 Security Testing

### Automated Security Scans
The project includes automated security scanning:

```bash
# Run security scans
bandit -r app/                    # Python security linter
safety check                     # Dependency vulnerability check
pytest tests/test_security.py    # Security-focused tests
```

### Manual Security Testing

#### 1. Authentication Testing
```bash
# Test invalid credentials
curl -X POST /api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"invalid@test.com","password":"wrong"}'

# Test token expiration
curl -X GET /api/items \
  -H "Authorization: Bearer expired_token"
```

#### 2. Input Validation Testing
```bash
# Test XSS prevention
curl -X POST /api/items \
  -H "Authorization: Bearer valid_token" \
  -H "Content-Type: application/json" \
  -d '{"title":"<script>alert(\"xss\")</script>","price":10}'

# Test SQL injection prevention
curl -X GET "/api/items?search='; DROP TABLE users; --"
```

#### 3. Rate Limiting Testing
```bash
# Test rate limiting
for i in {1..20}; do
  curl -X POST /api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}'
done
```

## 🚨 Incident Response

### Security Incident Checklist

1. **Immediate Response**
   - [ ] Identify the scope of the incident
   - [ ] Contain the threat (block IPs, disable accounts)
   - [ ] Preserve evidence (logs, database snapshots)

2. **Investigation**
   - [ ] Analyze logs for attack patterns
   - [ ] Check for data exfiltration
   - [ ] Identify affected users/data

3. **Recovery**
   - [ ] Patch vulnerabilities
   - [ ] Reset compromised credentials
   - [ ] Update security measures

4. **Post-Incident**
   - [ ] Document lessons learned
   - [ ] Update security procedures
   - [ ] Notify stakeholders if required

### Log Analysis
Use correlation IDs to trace security incidents:

```bash
# Find all requests from a specific correlation ID
grep "correlation_id=abc-123" logs/app.log

# Analyze failed login attempts
grep "failed login" logs/app.log | grep "$(date +%Y-%m-%d)"
```

## 📋 Security Checklist

### Pre-Deployment Security Review

- [ ] All secrets are in environment variables
- [ ] HTTPS is enforced
- [ ] Security headers are configured
- [ ] Input validation is comprehensive
- [ ] Error messages don't leak information
- [ ] Rate limiting is configured
- [ ] Logging captures security events
- [ ] Dependencies are up to date
- [ ] Security tests pass
- [ ] Database permissions are minimal

### Regular Security Maintenance

- [ ] Update dependencies monthly
- [ ] Review access logs weekly
- [ ] Rotate secrets quarterly
- [ ] Conduct security scans weekly
- [ ] Review user permissions monthly
- [ ] Update security documentation
- [ ] Train team on security practices

## 🔗 Security Resources

### Tools
- [Bandit](https://bandit.readthedocs.io/) - Python security linter
- [Safety](https://pyup.io/safety/) - Dependency vulnerability scanner
- [OWASP ZAP](https://owasp.org/www-project-zap/) - Web application security scanner

### References
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [JWT Security Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)

## 📞 Reporting Security Issues

If you discover a security vulnerability, please:

1. **Do not** open a public GitHub issue
2. Email security concerns to: startabase@gmail.com
3. Include detailed information about the vulnerability
4. Allow time for the team to respond and fix the issue

We appreciate responsible disclosure and will acknowledge security researchers who help improve our security.
