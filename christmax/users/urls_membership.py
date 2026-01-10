"""
URL configuration for membership system.
"""
from django.urls import path
from .views_membership import (
    MembershipPlansView,
    MySubscriptionView,
    UpgradeToPremiumView,
    ProcessUpgradeView,
    CancelSubscriptionView,
    RenewSubscriptionView,
    CheckoutView,
)

app_name = 'membership'

urlpatterns = [
    # Public views
    path('plans/', MembershipPlansView.as_view(), name='plans'),
    
    # User subscription management
    path('my-subscription/', MySubscriptionView.as_view(), name='my_subscription'),
    path('upgrade/', UpgradeToPremiumView.as_view(), name='upgrade_to_premium'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    
    # Actions
    path('process-upgrade/', ProcessUpgradeView.as_view(), name='process_upgrade'),
    path('cancel/', CancelSubscriptionView.as_view(), name='cancel_subscription'),
    path('renew/', RenewSubscriptionView.as_view(), name='renew_subscription'),
]
