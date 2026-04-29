"""
Custom middleware for security and cache control
"""
from django.utils.deprecation import MiddlewareMixin


class NoCacheMiddleware(MiddlewareMixin):
    """
    Prevents caching of authenticated pages to avoid back button access after logout.
    Adds Cache-Control headers to prevent browser from caching pages.
    """
    
    def process_response(self, request, response):
        # Add cache control headers to prevent back button access
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Adds additional security headers to all responses
    """
    
    def process_response(self, request, response):
        # Prevent clickjacking
        response['X-Frame-Options'] = 'SAMEORIGIN'
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        # Enable XSS protection in older browsers
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response
