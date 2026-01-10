"""
Decorators for membership/subscription-based access control.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied


def premium_required(view_func=None, redirect_url='/membership/upgrade/'):
    """
    Decorator to require premium membership for a view.
    
    Usage:
        @premium_required
        def my_view(request):
            ...
    
        @premium_required(redirect_url='/custom-upgrade/')
        def my_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, _('Please login to access this feature.'))
                return redirect('account_login')
            
            if not request.user.has_premium_access():
                messages.warning(
                    request,
                    _('This feature is only available to Premium members. Please upgrade your membership.')
                )
                return redirect(redirect_url)
            
            return func(request, *args, **kwargs)
        return wrapper
    
    # Allow using @premium_required or @premium_required()
    if view_func:
        return decorator(view_func)
    return decorator


def feature_required(feature_name, redirect_url='/membership/upgrade/'):
    """
    Decorator to require a specific feature from user's plan.
    
    Usage:
        @feature_required('can_enter_competitions')
        def competition_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, _('Please login to access this feature.'))
                return redirect('account_login')
            
            if not request.user.can_access_feature(feature_name):
                messages.warning(
                    request,
                    _('Your current plan does not include this feature. Please upgrade your membership.')
                )
                return redirect(redirect_url)
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def subscription_active_required(view_func):
    """
    Decorator to ensure user has an active subscription (any tier).
    
    Usage:
        @subscription_active_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, _('Please login to continue.'))
            return redirect('account_login')
        
        subscription = request.user.get_active_subscription()
        if not subscription or not subscription.is_active():
            messages.error(
                request,
                _('Your subscription has expired. Please renew or upgrade your membership.')
            )
            return redirect('membership_plans')
        
        return func(request, *args, **kwargs)
    return wrapper
