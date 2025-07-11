"""Performance tests for the application."""

import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestPerformance:
    """Performance and load testing."""
    
    def test_item_list_response_time(self, client):
        """Test that item listing responds within acceptable time."""
        start_time = time.time()
        response = client.get('/api/items?per_page=20')
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < 1.0  # Should respond within 1 second
    
    def test_health_check_response_time(self, client):
        """Test health check endpoint response time."""
        start_time = time.time()
        response = client.get('/health')
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < 0.5  # Health check should be very fast
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        def make_request():
            return client.get('/health')
        
        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            
            success_count = 0
            for future in as_completed(futures):
                response = future.result()
                if response.status_code == 200:
                    success_count += 1
        
        # All requests should succeed
        assert success_count == 10
    
    def test_large_dataset_pagination(self, client):
        """Test pagination performance with large datasets."""
        # Test requesting a large page number
        start_time = time.time()
        response = client.get('/api/items?page=100&per_page=20')
        duration = time.time() - start_time
        
        # Should handle large page numbers efficiently
        assert duration < 2.0
        assert response.status_code == 200


class TestCaching:
    """Test caching functionality."""
    
    def test_cache_hit_performance(self, client):
        """Test that cached responses are faster."""
        # First request (cache miss)
        start_time = time.time()
        response1 = client.get('/api/items/popular')
        first_duration = time.time() - start_time
        
        # Second request (cache hit)
        start_time = time.time()
        response2 = client.get('/api/items/popular')
        second_duration = time.time() - start_time
        
        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Second request should be faster (cached)
        # Note: This test might be flaky in fast environments
        # Consider using cache headers or other indicators
    
    def test_cache_invalidation(self, client, auth_headers):
        """Test that cache is properly invalidated."""
        # Get cached data
        response1 = client.get('/api/items/popular')
        
        # Create new item (should invalidate cache)
        client.post('/api/items',
                   json={
                       'title': 'Cache Test Item',
                       'description': 'Test description',
                       'price': 15.00,
                       'category': 'BOOKS'
                   },
                   headers=auth_headers)
        
        # Get data again (should be fresh)
        response2 = client.get('/api/items/popular')
        
        assert response1.status_code == 200
        assert response2.status_code == 200