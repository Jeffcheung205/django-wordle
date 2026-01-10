"""
Views for membership and subscription management.
"""
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import SubscriptionPlan, UserSubscription, MembershipTier


class MembershipPlansView(ListView):
    """
    Display all available membership plans.
    Public view accessible to anyone.
    """
    model = SubscriptionPlan
    template_name = 'membership/plans.html'
    context_object_name = 'plans'
    
    def get_queryset(self):
        """Get only active plans, ordered by price."""
        return SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            context['current_subscription'] = self.request.user.get_active_subscription()
        
        return context


class MySubscriptionView(LoginRequiredMixin, TemplateView):
    """
    Display user's current subscription details and history.
    """
    template_name = 'membership/my_subscription.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        context['current_subscription'] = user.get_active_subscription()
        context['subscription_history'] = user.subscriptions.all().order_by('-created_at')[:10]
        
        return context


class UpgradeToPremiumView(LoginRequiredMixin, TemplateView):
    """
    Upgrade page showing premium benefits and payment options.
    """
    template_name = 'membership/upgrade.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get premium plan
        try:
            premium_plan = SubscriptionPlan.objects.get(
                tier=MembershipTier.PREMIUM,
                is_active=True
            )
            context['premium_plan'] = premium_plan
        except SubscriptionPlan.DoesNotExist:
            messages.error(self.request, _('Premium plan not available at this time.'))
        
        context['current_subscription'] = self.request.user.get_active_subscription()
        
        return context


class ProcessUpgradeView(LoginRequiredMixin, View):
    """
    Process the upgrade to premium membership.
    This is a placeholder - integrate with payment gateway (Stripe/PayPal).
    """
    
    def post(self, request, *args, **kwargs):
        plan_id = request.POST.get('plan_id')
        payment_method = request.POST.get('payment_method', 'manual')
        
        try:
            plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
            
            # Cancel current active subscriptions
            current_subscription = request.user.get_active_subscription()
            if current_subscription:
                current_subscription.cancel()
            
            # Create new subscription (1 month duration for paid plans)
            end_date = None
            if not plan.is_free():
                end_date = timezone.now() + timedelta(days=30)
            
            new_subscription = UserSubscription.objects.create(
                user=request.user,
                plan=plan,
                status=UserSubscription.SubscriptionStatus.ACTIVE,
                end_date=end_date,
                payment_method=payment_method,
                # TODO: Add transaction_id from payment gateway
            )
            
            messages.success(
                request,
                _('Successfully upgraded to {plan_name}!').format(plan_name=plan.name)
            )
            
            return redirect('my_subscription')
            
        except Exception as e:
            messages.error(request, _('Failed to process upgrade. Please try again.'))
            return redirect('upgrade_to_premium')


class CancelSubscriptionView(LoginRequiredMixin, View):
    """
    Cancel user's current subscription.
    """
    
    def post(self, request, *args, **kwargs):
        subscription = request.user.get_active_subscription()
        
        if not subscription:
            messages.warning(request, _('No active subscription to cancel.'))
            return redirect('my_subscription')
        
        if subscription.plan.is_free():
            messages.warning(request, _('Cannot cancel free plan.'))
            return redirect('my_subscription')
        
        subscription.cancel()
        
        messages.success(
            request,
            _('Your subscription has been cancelled. You will still have access until the end of your billing period.')
        )
        
        return redirect('my_subscription')


class RenewSubscriptionView(LoginRequiredMixin, View):
    """
    Renew user's expired subscription.
    """
    
    def post(self, request, *args, **kwargs):
        subscription_id = request.POST.get('subscription_id')
        months = int(request.POST.get('months', 1))
        
        try:
            subscription = get_object_or_404(
                UserSubscription,
                id=subscription_id,
                user=request.user
            )
            
            # TODO: Process payment before renewing
            
            subscription.renew(months=months)
            
            messages.success(
                request,
                _('Successfully renewed your subscription for {months} month(s)!').format(months=months)
            )
            
        except Exception as e:
            messages.error(request, _('Failed to renew subscription. Please try again.'))
        
        return redirect('my_subscription')


class CheckoutView(LoginRequiredMixin, TemplateView):
    """
    Checkout page for payment processing.
    Integrate with Stripe or PayPal here.
    """
    template_name = 'membership/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        plan_id = self.request.GET.get('plan_id')
        if plan_id:
            try:
                context['selected_plan'] = SubscriptionPlan.objects.get(
                    id=plan_id,
                    is_active=True
                )
            except SubscriptionPlan.DoesNotExist:
                messages.error(self.request, _('Selected plan not found.'))
        
        # TODO: Add Stripe publishable key or PayPal client ID
        # context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        
        return context
