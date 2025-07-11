"""Monitoring and health check middleware."""

from flask import Blueprint, jsonify, current_app
from datetime import datetime, timezone
import psutil
import time
from ..extensions import db
from ..models import User, Item


monitoring_bp = Blueprint('monitoring', __name__)


@monitoring_bp.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint."""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0',
        'checks': {}
    }
    
    overall_healthy = True
    
    # Database connectivity check
    try:
        db.session.execute('SELECT 1')
        health_status['checks']['database'] = {
            'status': 'healthy',
            'response_time_ms': 0  # Could measure actual response time
        }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_healthy = False
    
    # Redis cache check
    try:
        from .caching import cache_manager
        if cache_manager.redis_client:
            cache_manager.redis_client.ping()
            health_status['checks']['cache'] = {'status': 'healthy'}
        else:
            health_status['checks']['cache'] = {'status': 'unavailable'}
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # System resources check
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status['checks']['system'] = {
            'status': 'healthy',
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent
        }
        
        # Alert if resources are high
        if cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
            health_status['checks']['system']['status'] = 'warning'
            
    except Exception as e:
        health_status['checks']['system'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Set overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
        return jsonify(health_status), 503
    
    return jsonify(health_status), 200


@monitoring_bp.route('/metrics', methods=['GET'])
def metrics():
    """Basic application metrics."""
    try:
        # Database metrics
        total_users = User.query.count()
        active_users = User.query.filter_by(account_status='Active').count()
        total_items = Item.query.count()
        available_items = Item.query.filter_by(status='Available').count()
        
        metrics_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': {
                'total_users': total_users,
                'active_users': active_users,
                'total_items': total_items,
                'available_items': available_items
            },
            'system': {
                'uptime_seconds': time.time() - current_app.start_time if hasattr(current_app, 'start_time') else 0
            }
        }
        
        return jsonify(metrics_data), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to collect metrics',
            'details': str(e)
        }), 500


@monitoring_bp.route('/ready', methods=['GET'])
def readiness_check():
    """Kubernetes readiness probe endpoint."""
    try:
        # Check if application is ready to serve traffic
        db.session.execute('SELECT 1')
        return jsonify({'status': 'ready'}), 200
    except Exception:
        return jsonify({'status': 'not ready'}), 503


@monitoring_bp.route('/live', methods=['GET'])
def liveness_check():
    """Kubernetes liveness probe endpoint."""
    # Simple liveness check - if we can respond, we're alive
    return jsonify({'status': 'alive'}), 200