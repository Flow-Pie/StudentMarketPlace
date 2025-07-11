"""
Monitoring and health check middleware.
"""
import logging
import time
import psutil
import os
from flask import jsonify, current_app, g
from sqlalchemy import text
from app.extensions import db

logger = logging.getLogger(__name__)

class HealthChecker:
    """Health check utilities for monitoring."""
    
    @staticmethod
    def check_database():
        """Check database connectivity."""
        try:
            # Simple query to test database connection
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            return {'status': 'healthy', 'response_time': 0}
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {'status': 'unhealthy', 'error': str(e)}
    
    @staticmethod
    def check_system_resources():
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'status': 'healthy',
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available // (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free // (1024 * 1024 * 1024)
            }
        except Exception as e:
            logger.error(f"System resource check failed: {str(e)}")
            return {'status': 'unhealthy', 'error': str(e)}
    
    @staticmethod
    def get_application_metrics():
        """Get application-specific metrics."""
        try:
            from app.middleware.caching import cache_manager
            
            # Get cache statistics
            cache_stats = cache_manager.get_stats()
            
            # Get basic app info
            metrics = {
                'app_name': current_app.config.get('APP_NAME', 'StudentMarketplace'),
                'version': current_app.config.get('VERSION', '1.0.0'),
                'environment': current_app.config.get('FLASK_ENV', 'production'),
                'uptime_seconds': time.time() - current_app.config.get('START_TIME', time.time()),
                'cache_stats': cache_stats
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Application metrics check failed: {str(e)}")
            return {'error': str(e)}


def create_health_endpoints(app):
    """Create health check endpoints."""
    
    @app.route('/health')
    def health_check():
        """Basic health check endpoint."""
        try:
            # Check database
            db_health = HealthChecker.check_database()
            
            # Check system resources
            system_health = HealthChecker.check_system_resources()
            
            # Determine overall health
            overall_status = 'healthy'
            if db_health['status'] != 'healthy' or system_health['status'] != 'healthy':
                overall_status = 'unhealthy'
            
            response = {
                'status': overall_status,
                'timestamp': time.time(),
                'checks': {
                    'database': db_health,
                    'system': system_health
                }
            }
            
            status_code = 200 if overall_status == 'healthy' else 503
            return jsonify(response), status_code
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }), 503
    
    @app.route('/ready')
    def readiness_check():
        """Readiness check for Kubernetes."""
        try:
            # Check if app is ready to serve requests
            db_health = HealthChecker.check_database()
            
            if db_health['status'] == 'healthy':
                return jsonify({
                    'status': 'ready',
                    'timestamp': time.time()
                }), 200
            else:
                return jsonify({
                    'status': 'not_ready',
                    'reason': 'database_unavailable',
                    'timestamp': time.time()
                }), 503
                
        except Exception as e:
            logger.error(f"Readiness check failed: {str(e)}")
            return jsonify({
                'status': 'not_ready',
                'error': str(e),
                'timestamp': time.time()
            }), 503
    
    @app.route('/live')
    def liveness_check():
        """Liveness check for Kubernetes."""
        # Simple liveness check - if we can respond, we're alive
        return jsonify({
            'status': 'alive',
            'timestamp': time.time()
        }), 200
    
    @app.route('/metrics')
    def metrics_endpoint():
        """Application metrics endpoint."""
        try:
            metrics = HealthChecker.get_application_metrics()
            system_health = HealthChecker.check_system_resources()
            
            response = {
                'application': metrics,
                'system': system_health,
                'timestamp': time.time()
            }
            
            return jsonify(response), 200
            
        except Exception as e:
            logger.error(f"Metrics endpoint failed: {str(e)}")
            return jsonify({
                'error': str(e),
                'timestamp': time.time()
            }), 500


class RequestMetrics:
    """Track request metrics."""
    
    def __init__(self):
        self.request_count = 0
        self.response_times = []
        self.error_count = 0
    
    def record_request(self, response_time, status_code):
        """Record request metrics."""
        self.request_count += 1
        self.response_times.append(response_time)
        
        if status_code >= 400:
            self.error_count += 1
        
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def get_stats(self):
        """Get request statistics."""
        if not self.response_times:
            return {
                'request_count': self.request_count,
                'error_count': self.error_count,
                'error_rate': 0,
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0
            }
        
        avg_response_time = sum(self.response_times) / len(self.response_times)
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': round(error_rate, 2),
            'avg_response_time': round(avg_response_time, 3),
            'min_response_time': round(min(self.response_times), 3),
            'max_response_time': round(max(self.response_times), 3)
        }


# Global metrics instance
request_metrics = RequestMetrics()


def init_monitoring(app):
    """Initialize monitoring middleware."""
    
    # Record start time
    app.config['START_TIME'] = time.time()
    
    # Create health endpoints
    create_health_endpoints(app)
    
    @app.before_request
    def before_request():
        """Record request start time."""
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Record request metrics."""
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            request_metrics.record_request(response_time, response.status_code)
        
        return response