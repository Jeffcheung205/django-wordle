"""
Example usage of the membership system.

This file demonstrates how to use the membership system in your views, templates, and models.
"""

# ============================================================================
# 1. PROTECTING VIEWS WITH DECORATORS
# ============================================================================

from django.shortcuts import render
from users.decorators import premium_required, feature_required


@premium_required
def premium_quiz_view(request):
    """Only premium members can access this quiz."""
    return render(request, 'quizzes/premium_quiz.html')


@feature_required('can_enter_competitions')
def competition_entry_view(request):
    """Only users with competition access can enter."""
    return render(request, 'competitions/entry.html')


# Custom redirect URL
@premium_required(redirect_url='/pricing/')
def custom_redirect_view(request):
    """Redirects to custom URL if not premium."""
    return render(request, 'premium_content.html')


# ============================================================================
# 2. USING CLASS-BASED VIEW MIXINS
# ============================================================================

from django.views.generic import ListView, DetailView
from users.mixins import PremiumRequiredMixin, FeatureRequiredMixin


class PremiumQuizListView(PremiumRequiredMixin, ListView):
    """List view accessible only to premium members."""
    model = Quiz
    template_name = 'quizzes/premium_list.html'
    context_object_name = 'quizzes'


class CompetitionDetailView(FeatureRequiredMixin, DetailView):
    """Competition detail requiring specific feature."""
    model = Competition
    template_name = 'competitions/detail.html'
    required_feature = 'can_enter_competitions'


# ============================================================================
# 3. CHECKING MEMBERSHIP IN VIEWS
# ============================================================================

def adaptive_quiz_view(request):
    """Show different content based on membership level."""
    
    # Get user's subscription
    subscription = request.user.get_active_subscription()
    
    # Check premium access
    is_premium = request.user.has_premium_access()
    
    # Check specific feature
    has_analytics = request.user.can_access_feature('has_detailed_analytics')
    
    # Get quiz limit
    daily_limit = subscription.plan.daily_quiz_limit if subscription else 5
    
    context = {
        'is_premium': is_premium,
        'has_analytics': has_analytics,
        'daily_limit': daily_limit,
        'subscription': subscription,
    }
    
    return render(request, 'quizzes/adaptive.html', context)


# ============================================================================
# 4. HANDLING SUBSCRIPTION IN VIEWS
# ============================================================================

from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def check_quiz_limit(request):
    """Check if user can take more quizzes today."""
    
    subscription = request.user.get_active_subscription()
    
    if not subscription:
        messages.error(request, 'Please subscribe to take quizzes.')
        return redirect('membership:plans')
    
    # Check daily limit (0 = unlimited)
    if subscription.plan.daily_quiz_limit > 0:
        # TODO: Implement quiz tracking
        quizzes_taken_today = get_user_quiz_count_today(request.user)
        
        if quizzes_taken_today >= subscription.plan.daily_quiz_limit:
            messages.warning(
                request,
                f'You have reached your daily limit of {subscription.plan.daily_quiz_limit} quizzes. '
                f'Upgrade to Premium for unlimited access!'
            )
            return redirect('membership:upgrade_to_premium')
    
    return render(request, 'quizzes/start.html')


# ============================================================================
# 5. TEMPLATE USAGE EXAMPLES
# ============================================================================

"""
<!-- templates/quizzes/quiz_page.html -->
{% load i18n %}

<!-- Check if user is premium -->
{% if user.has_premium_access %}
    <div class="premium-badge">
        <i class="bi bi-star-fill"></i> Premium Member
    </div>
{% endif %}

<!-- Show features based on plan -->
{% if user.can_access_feature 'has_progress_tracking' %}
    <div class="progress-tracker">
        <!-- Show progress charts -->
    </div>
{% else %}
    <div class="upgrade-prompt">
        <p>Upgrade to Premium to track your progress!</p>
        <a href="{% url 'membership:upgrade_to_premium' %}">Upgrade Now</a>
    </div>
{% endif %}

<!-- Display subscription info -->
{% with subscription=user.get_active_subscription %}
    {% if subscription %}
        <div class="subscription-info">
            <h4>Your Plan: {{ subscription.plan.name }}</h4>
            
            {% if subscription.plan.daily_quiz_limit == 0 %}
                <p>Unlimited quizzes</p>
            {% else %}
                <p>{{ subscription.plan.daily_quiz_limit }} quizzes per day</p>
            {% endif %}
            
            {% if subscription.end_date %}
                <p>Renews: {{ subscription.end_date|date:"F d, Y" }}</p>
            {% endif %}
        </div>
    {% endif %}
{% endwith %}

<!-- Feature gates -->
{% if not user.is_authenticated %}
    <a href="{% url 'account_login' %}">Login to access quizzes</a>

{% elif not user.has_premium_access %}
    <div class="free-tier-message">
        <h5>Free Tier Limitations</h5>
        <ul>
            <li>5 quizzes per day</li>
            <li>Limited question access</li>
        </ul>
        <a href="{% url 'membership:plans' %}" class="btn btn-primary">
            Upgrade to Premium
        </a>
    </div>

{% else %}
    <!-- Show premium content -->
    <div class="premium-content">
        <!-- Unlimited access content -->
    </div>
{% endif %}
"""


# ============================================================================
# 6. MODEL METHODS USAGE
# ============================================================================

from users.models import User, SubscriptionPlan, UserSubscription, MembershipTier
from django.utils import timezone
from datetime import timedelta


def example_model_operations():
    """Examples of working with subscription models."""
    
    # Get a user
    user = User.objects.get(email='user@example.com')
    
    # Check their subscription
    subscription = user.get_active_subscription()
    print(f"User plan: {subscription.plan.name}")
    print(f"Is premium: {user.has_premium_access()}")
    
    # Check specific features
    can_compete = user.can_access_feature('can_enter_competitions')
    has_tracking = user.can_access_feature('has_progress_tracking')
    
    # Get all subscription plans
    plans = SubscriptionPlan.objects.filter(is_active=True)
    
    # Get premium plan
    premium = SubscriptionPlan.objects.get(tier=MembershipTier.PREMIUM)
    
    # Create a new subscription (e.g., after payment)
    new_subscription = UserSubscription.objects.create(
        user=user,
        plan=premium,
        status=UserSubscription.SubscriptionStatus.ACTIVE,
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=30),
        payment_method='stripe',
        transaction_id='ch_abc123xyz',
    )
    
    # Cancel subscription
    if subscription:
        subscription.cancel()
    
    # Renew subscription
    if subscription:
        subscription.renew(months=1)
    
    # Check days remaining
    if subscription and subscription.end_date:
        days = subscription.days_remaining()
        print(f"Days remaining: {days}")


# ============================================================================
# 7. CUSTOM SUBSCRIPTION LOGIC
# ============================================================================

def grant_trial_subscription(user):
    """Grant a 7-day trial of premium."""
    
    premium = SubscriptionPlan.objects.get(tier=MembershipTier.PREMIUM)
    
    # Cancel existing subscriptions
    user.subscriptions.filter(status='ACTIVE').update(status='CANCELLED')
    
    # Create trial subscription
    trial = UserSubscription.objects.create(
        user=user,
        plan=premium,
        status=UserSubscription.SubscriptionStatus.TRIAL,
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=7),
        payment_method='trial',
    )
    
    return trial


def check_subscription_expiry():
    """Check for expiring subscriptions (run via cron/celery)."""
    
    from django.core.mail import send_mail
    
    # Get subscriptions expiring in 3 days
    expiring_soon = UserSubscription.objects.filter(
        status='ACTIVE',
        end_date__lte=timezone.now() + timedelta(days=3),
        end_date__gte=timezone.now()
    )
    
    for subscription in expiring_soon:
        # Send reminder email
        send_mail(
            subject='Your subscription is expiring soon',
            message=f'Your {subscription.plan.name} subscription expires in {subscription.days_remaining()} days.',
            from_email='noreply@example.com',
            recipient_list=[subscription.user.email],
        )


# ============================================================================
# 8. SIGNALS AND AUTO-SUBSCRIPTION
# ============================================================================

"""
The following happens automatically via signals in models.py:

1. When a user is created:
   - Profile is created
   - Free subscription is automatically assigned
   - User can start using basic features immediately

2. When a subscription is upgraded:
   - Previous subscription is cancelled
   - New subscription is activated
   - User immediately gets new features

No manual subscription creation needed for new users!
"""


# ============================================================================
# 9. ADMIN ACTIONS
# ============================================================================

"""
Admin actions available at /admin/users/usersubscription/:

- Activate selected subscriptions
- Cancel selected subscriptions  
- Mark selected as expired

Admin can also:
- View subscriber statistics per plan
- Filter by status, plan, payment method
- Search by user email or transaction ID
- View subscription history
"""


# ============================================================================
# 10. API/AJAX USAGE (Optional)
# ============================================================================

from django.http import JsonResponse


@login_required
def check_premium_api(request):
    """API endpoint to check user's premium status."""
    
    subscription = request.user.get_active_subscription()
    
    return JsonResponse({
        'is_premium': request.user.has_premium_access(),
        'plan_name': subscription.plan.name if subscription else None,
        'features': {
            'unlimited_quizzes': subscription.plan.daily_quiz_limit == 0 if subscription else False,
            'can_compete': request.user.can_access_feature('can_enter_competitions'),
            'has_analytics': request.user.can_access_feature('has_detailed_analytics'),
        },
        'days_remaining': subscription.days_remaining() if subscription else None,
    })


"""
// JavaScript usage
fetch('/api/check-premium/')
    .then(response => response.json())
    .then(data => {
        if (data.is_premium) {
            document.querySelector('.premium-features').style.display = 'block';
        } else {
            document.querySelector('.upgrade-prompt').style.display = 'block';
        }
    });
"""
