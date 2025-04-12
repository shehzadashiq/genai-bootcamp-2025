import logging
import time

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    """Middleware to log all requests and responses."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Log request
        start_time = time.time()
        
        # Log the request details
        logger.info(f"Request: {request.method} {request.path}")
        logger.debug(f"Request headers: {dict(request.headers)}")
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log the response details
        logger.info(f"Response: {request.method} {request.path} - Status: {response.status_code} - Duration: {duration:.2f}s")
        
        return response
