"""
Middleware for membership system.
"""
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone


class SubscriptionCheckMiddleware(MiddlewareMixin):
    """
    Middleware to check and update subscription status on each request.
    Automatically expires subscriptions that have passed their end_date.
    """
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Check for expired subscriptions
            subscription = request.user.get_active_subscription()
            if subscription and subscription.end_date:
                if subscription.end_date < timezone.now() and subscription.status == 'ACTIVE':
                    # Auto-expire subscription
                    subscription.status = 'EXPIRED'
                    subscription.save()
                    
                    # Store in request for displaying messages in views
                    request.subscription_expired = True
        
        return None
