"""
Mixins for class-based views requiring membership/subscription checks.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


class PremiumRequiredMixin(LoginRequiredMixin):
    """
    Mixin to require premium membership for class-based views.
    
    Usage:
        class MyView(PremiumRequiredMixin, View):
            ...
    """
    premium_redirect_url = '/membership/upgrade/'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not request.user.has_premium_access():
            messages.warning(
                request,
                _('This feature is only available to Premium members. Please upgrade your membership.')
            )
            return redirect(self.premium_redirect_url)
        
        return super().dispatch(request, *args, **kwargs)


class FeatureRequiredMixin(LoginRequiredMixin):
    """
    Mixin to require a specific feature from user's plan.
    
    Usage:
        class CompetitionView(FeatureRequiredMixin, View):
            required_feature = 'can_enter_competitions'
            ...
    """
    required_feature = None
    feature_redirect_url = '/membership/upgrade/'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if self.required_feature and not request.user.can_access_feature(self.required_feature):
            messages.warning(
                request,
                _('Your current plan does not include this feature. Please upgrade your membership.')
            )
            return redirect(self.feature_redirect_url)
        
        return super().dispatch(request, *args, **kwargs)


class SubscriptionActiveRequiredMixin(LoginRequiredMixin):
    """
    Mixin to ensure user has an active subscription (any tier).
    
    Usage:
        class MyView(SubscriptionActiveRequiredMixin, View):
            ...
    """
    subscription_redirect_url = '/membership/plans/'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        subscription = request.user.get_active_subscription()
        if not subscription or not subscription.is_active():
            messages.error(
                request,
                _('Your subscription has expired. Please renew or upgrade your membership.')
            )
            return redirect(self.subscription_redirect_url)
        
        return super().dispatch(request, *args, **kwargs)
