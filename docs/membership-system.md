# Membership System Documentation

## Overview

The membership system provides subscription-based access control with two tiers:
- **Free**: Basic access with limited features
- **Premium**: Full access with all features unlocked (HK$20/month)

## Features

### Subscription Plans

Plans are configured with the following features:

**Free Plan:**
- 5 quiz attempts per day
- Basic categories access
- View leaderboard
- ❌ No progress tracking
- ❌ No competition entry
- ❌ No detailed analytics
- ❌ No certificates
- ❌ Ads present

**Premium Plan (HK$20/month):**
- ✅ Unlimited quiz attempts
- ✅ All 100+ questions
- ✅ Enter competitions
- ✅ Progress tracking
- ✅ Detailed analytics
- ✅ Certificate of completion
- ✅ Ad-free experience

## Architecture

### Models

#### `SubscriptionPlan`
Defines available subscription plans with features and pricing.

```python
from users.models import SubscriptionPlan, MembershipTier

# Get all active plans
plans = SubscriptionPlan.objects.filter(is_active=True)

# Get premium plan
premium = SubscriptionPlan.objects.get(tier=MembershipTier.PREMIUM)
```

#### `UserSubscription`
Tracks user's current and historical subscriptions.

```python
from users.models import UserSubscription

# Get user's active subscription
subscription = request.user.get_active_subscription()

# Check if active
if subscription and subscription.is_active():
    print(f"User has {subscription.plan.name}")
```

### User Methods

```python
# Check premium access
if request.user.has_premium_access():
    # Show premium content
    pass

# Check specific feature
if request.user.can_access_feature('can_enter_competitions'):
    # Allow competition entry
    pass

# Get active subscription
subscription = request.user.get_active_subscription()
```

## Access Control

### View Decorators

```python
from users.decorators import premium_required, feature_required

@premium_required
def premium_view(request):
    """Only accessible to premium members"""
    pass

@feature_required('can_enter_competitions')
def competition_view(request):
    """Requires specific feature"""
    pass
```

### Class-Based View Mixins

```python
from users.mixins import PremiumRequiredMixin, FeatureRequiredMixin

class PremiumOnlyView(PremiumRequiredMixin, TemplateView):
    template_name = 'premium.html'

class CompetitionView(FeatureRequiredMixin, ListView):
    required_feature = 'can_enter_competitions'
    model = Competition
```

### Template Usage

```django
{% if user.has_premium_access %}
    <div class="premium-content">
        <!-- Premium features -->
    </div>
{% else %}
    <a href="{% url 'membership:upgrade_to_premium' %}">Upgrade to Premium</a>
{% endif %}

<!-- Check specific feature -->
{% if user.can_access_feature 'has_progress_tracking' %}
    <!-- Show progress charts -->
{% endif %}
```

## URLs

The membership system provides the following URLs:

```python
# View all plans
/membership/plans/

# User's subscription dashboard
/membership/my-subscription/

# Upgrade page
/membership/upgrade/

# Checkout page
/membership/checkout/?plan_id=<id>

# Process upgrade (POST)
/membership/process-upgrade/

# Cancel subscription (POST)
/membership/cancel/

# Renew subscription (POST)
/membership/renew/
```

## Management Commands

### Create Default Plans

```bash
poetry run python manage.py create_plans
```

Creates or updates the default Free and Premium plans.

## Admin Interface

Access the membership admin at `/admin/`:

- **Subscription Plans**: Manage plans, features, and pricing
- **User Subscriptions**: View and manage user subscriptions
- Bulk actions: Activate, cancel, mark expired
- Statistics: Subscriber counts, active users

## Payment Integration

### Payment Gateway Setup (TODO)

The system is designed to integrate with payment gateways. To add payment processing:

1. **Stripe Integration** (Recommended):
   ```bash
   poetry add stripe
   ```

2. Update `ProcessUpgradeView` in `users/views_membership.py`:
   ```python
   import stripe
   stripe.api_key = settings.STRIPE_SECRET_KEY
   
   # Create payment intent
   intent = stripe.PaymentIntent.create(
       amount=int(plan.price_monthly * 100),
       currency='hkd',
       metadata={'user_id': request.user.id, 'plan_id': plan.id}
   )
   ```

3. Add webhook handler for payment confirmations:
   ```python
   @csrf_exempt
   def stripe_webhook(request):
       payload = request.body
       sig_header = request.META['HTTP_STRIPE_SIGNATURE']
       
       event = stripe.Webhook.construct_event(
           payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
       )
       
       if event['type'] == 'payment_intent.succeeded':
           # Activate subscription
           pass
   ```

4. Update settings.py:
   ```python
   STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
   STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
   STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
   ```

### Alternative Payment Providers

- **PayPal**: Use `django-paypal`
- **Alipay/WeChat Pay**: For Asian markets
- **Cryptocurrency**: Integrate with Coinbase Commerce

## Middleware

Add subscription check middleware to `settings.py`:

```python
MIDDLEWARE = [
    # ... other middleware
    'users.middleware.SubscriptionCheckMiddleware',
]
```

This automatically:
- Checks for expired subscriptions on each request
- Updates subscription status
- Sets `request.subscription_expired` flag

## Testing

### Create Test Subscriptions

```python
from users.models import User, SubscriptionPlan, UserSubscription, MembershipTier

# Create test user
user = User.objects.create_user(email='test@example.com', password='test123')

# Get premium plan
premium = SubscriptionPlan.objects.get(tier=MembershipTier.PREMIUM)

# Create subscription
subscription = UserSubscription.objects.create(
    user=user,
    plan=premium,
    status='ACTIVE',
    end_date=timezone.now() + timedelta(days=30)
)
```

### Test Access Control

```python
from django.test import TestCase

class MembershipTests(TestCase):
    def test_premium_access(self):
        user = User.objects.create_user(email='test@example.com')
        self.assertFalse(user.has_premium_access())
        
        # Upgrade to premium
        premium = SubscriptionPlan.objects.get(tier=MembershipTier.PREMIUM)
        UserSubscription.objects.create(
            user=user,
            plan=premium,
            status='ACTIVE'
        )
        
        self.assertTrue(user.has_premium_access())
```

## Database Schema

```
┌─────────────────────────────────┐
│      SubscriptionPlan           │
├─────────────────────────────────┤
│ PK  id                          │
│     name                        │
│     tier (FREE/PREMIUM)         │
│     price_monthly               │
│     daily_quiz_limit            │
│     can_enter_competitions      │
│     has_progress_tracking       │
│     has_detailed_analytics      │
│     has_certificates            │
│     is_ad_free                  │
│     access_all_questions        │
│     description                 │
│     is_active                   │
└─────────────────────────────────┘
              │
              │ 1:N
              ▼
┌─────────────────────────────────┐
│      UserSubscription           │
├─────────────────────────────────┤
│ PK  id                          │
│ FK  user_id                     │
│ FK  plan_id                     │
│     status (ACTIVE/EXPIRED...)  │
│     start_date                  │
│     end_date                    │
│     payment_method              │
│     transaction_id              │
│     auto_renew                  │
│     cancelled_at                │
└─────────────────────────────────┘
```

## Future Enhancements

1. **Trial Periods**: Add 7-day free trial for premium
2. **Promo Codes**: Discount code system
3. **Annual Plans**: Discounted yearly subscriptions
4. **Team Plans**: Multiple users per subscription
5. **Usage Analytics**: Track feature usage per plan
6. **Referral System**: Credits for referring friends
7. **Tiered Pricing**: Bronze, Silver, Gold tiers
8. **Grace Periods**: Allow access after expiration
9. **Subscription Pausing**: Temporary suspension
10. **Gift Subscriptions**: Purchase for others

## Support

For questions or issues with the membership system:
- Check the admin interface for subscription details
- Review logs in `UserSubscription` model
- Contact system administrator

## License

This membership system is part of the 天天好學 (FirstToBuzz) project.
