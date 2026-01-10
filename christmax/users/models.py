from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    """
    Custom User model that extends Django's AbstractUser.
    Keeps all default Django User fields + behaviors.

    Email-based authentication with optional username.
    """

    # Override email to make it unique and required
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={'unique': _('A user with that email already exists.')},
    )

    # Make username optional (auto-generated from email)
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        blank=True,  # Allow blank in forms
        null=False,  # But still required in DB
        help_text=_('Optional. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
    )

    # Use email as the primary identifier for auth
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Required for createsuperuser (beyond email)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users_user'  # Explicit table name

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        """Auto-generate username from email if not provided."""
        if not self.username:
            # Generate username from email: john.doe@example.com → john_doe
            local_part = self.email.split('@')[0]
            base_username = local_part.replace('.', '_').replace('+', '_')[:150]

            # Ensure uniqueness
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exclude(pk=self.pk).exists():
                username = f'{base_username}_{counter}'
                counter += 1

            self.username = username

        super().save(*args, **kwargs)
    
    def get_active_subscription(self):
        """Get user's current active subscription."""
        return self.subscriptions.filter(
            status='ACTIVE'
        ).select_related('plan').first()
    
    def has_premium_access(self):
        """Check if user has active premium subscription."""
        subscription = self.get_active_subscription()
        if not subscription:
            return False
        return subscription.plan.is_premium() and subscription.is_active()
    
    def can_access_feature(self, feature_name):
        """Check if user's plan includes a specific feature."""
        subscription = self.get_active_subscription()
        if not subscription or not subscription.is_active():
            return False
        return getattr(subscription.plan, feature_name, False)


class Profile(models.Model):
    """
    Extended user profile for game-specific data.
    Separated from User model for flexibility.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile', verbose_name=_('user')
    )

    player_level = models.PositiveIntegerField(
        _('player level'), default=1, help_text=_('Game progression level')
    )

    display_name = models.CharField(
        _('display name'), max_length=20, blank=True, help_text=_('Name shown to other players')
    )

    experience_points = models.PositiveIntegerField(_('experience points'), default=0)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')
        db_table = 'users_profile'

    def __str__(self):
        return f"{self.user.email}'s profile"


# Signals for auto-creating profiles
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create Profile when User is created."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save profile when user is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class MembershipTier(models.TextChoices):
    """Membership tier choices."""
    FREE = 'FREE', _('Free')
    PREMIUM = 'PREMIUM', _('Premium')


class SubscriptionPlan(models.Model):
    """
    Defines subscription plans (Free, Premium, etc.).
    Admin can configure features and pricing for each plan.
    """
    
    name = models.CharField(
        _('plan name'), max_length=50, unique=True,
        help_text=_('Display name for the plan (e.g., "Premium", "Free")')
    )
    
    tier = models.CharField(
        _('tier'), max_length=20, choices=MembershipTier.choices,
        default=MembershipTier.FREE, unique=True,
        help_text=_('Membership tier level')
    )
    
    price_monthly = models.DecimalField(
        _('monthly price'), max_digits=10, decimal_places=2, default=0,
        help_text=_('Price in HKD per month')
    )
    
    # Feature limits
    daily_quiz_limit = models.PositiveIntegerField(
        _('daily quiz limit'), default=5,
        help_text=_('Maximum quiz attempts per day (0 = unlimited)')
    )
    
    can_enter_competitions = models.BooleanField(
        _('can enter competitions'), default=False,
        help_text=_('Allow participation in competitions')
    )
    
    has_progress_tracking = models.BooleanField(
        _('has progress tracking'), default=False,
        help_text=_('Enable detailed progress analytics')
    )
    
    has_detailed_analytics = models.BooleanField(
        _('has detailed analytics'), default=False,
        help_text=_('Enable detailed performance analytics')
    )
    
    has_certificates = models.BooleanField(
        _('has certificates'), default=False,
        help_text=_('Enable certificate generation')
    )
    
    is_ad_free = models.BooleanField(
        _('ad-free experience'), default=False,
        help_text=_('Remove advertisements')
    )
    
    access_all_questions = models.BooleanField(
        _('access all questions'), default=False,
        help_text=_('Access to all 100+ questions')
    )
    
    # Metadata
    description = models.TextField(
        _('description'), blank=True,
        help_text=_('Short description of the plan')
    )
    
    is_active = models.BooleanField(
        _('is active'), default=True,
        help_text=_('Whether this plan is available for new subscriptions')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('subscription plan')
        verbose_name_plural = _('subscription plans')
        db_table = 'users_subscription_plan'
        ordering = ['price_monthly']
    
    def __str__(self):
        return f"{self.name} (HK${self.price_monthly}/month)"
    
    def is_free(self):
        """Check if this is a free plan."""
        return self.tier == MembershipTier.FREE
    
    def is_premium(self):
        """Check if this is a premium plan."""
        return self.tier == MembershipTier.PREMIUM


class UserSubscription(models.Model):
    """
    Tracks user's current and historical subscriptions.
    Each user has one active subscription at a time.
    """
    
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        EXPIRED = 'EXPIRED', _('Expired')
        CANCELLED = 'CANCELLED', _('Cancelled')
        TRIAL = 'TRIAL', _('Trial')
    
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('user')
    )
    
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_('plan')
    )
    
    status = models.CharField(
        _('status'), max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE
    )
    
    # Subscription period
    start_date = models.DateTimeField(
        _('start date'), default=timezone.now,
        help_text=_('When the subscription started')
    )
    
    end_date = models.DateTimeField(
        _('end date'), null=True, blank=True,
        help_text=_('When the subscription expires (null = indefinite)')
    )
    
    # Payment tracking
    payment_method = models.CharField(
        _('payment method'), max_length=50, blank=True,
        help_text=_('e.g., "stripe", "paypal", "manual"')
    )
    
    transaction_id = models.CharField(
        _('transaction ID'), max_length=255, blank=True,
        help_text=_('External payment transaction reference')
    )
    
    # Auto-renewal
    auto_renew = models.BooleanField(
        _('auto-renew'), default=False,
        help_text=_('Automatically renew subscription')
    )
    
    cancelled_at = models.DateTimeField(
        _('cancelled at'), null=True, blank=True,
        help_text=_('When the user cancelled the subscription')
    )
    
    # Metadata
    notes = models.TextField(
        _('notes'), blank=True,
        help_text=_('Internal notes about this subscription')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('user subscription')
        verbose_name_plural = _('user subscriptions')
        db_table = 'users_subscription'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"
    
    def is_active(self):
        """Check if subscription is currently active."""
        if self.status != self.SubscriptionStatus.ACTIVE:
            return False
        if self.end_date and self.end_date < timezone.now():
            return False
        return True
    
    def days_remaining(self):
        """Calculate days remaining in subscription."""
        if not self.end_date:
            return None  # Indefinite
        remaining = (self.end_date - timezone.now()).days
        return max(0, remaining)
    
    def cancel(self):
        """Cancel the subscription."""
        self.status = self.SubscriptionStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.auto_renew = False
        self.save()
    
    def renew(self, months=1):
        """Renew subscription for specified months."""
        if self.end_date and self.end_date > timezone.now():
            # Extend from current end date
            new_end_date = self.end_date + timedelta(days=30 * months)
        else:
            # Start fresh from now
            new_end_date = timezone.now() + timedelta(days=30 * months)
        
        self.end_date = new_end_date
        self.status = self.SubscriptionStatus.ACTIVE
        self.save()


# Signal to create default free subscription for new users
@receiver(post_save, sender=User)
def create_default_subscription(sender, instance, created, **kwargs):
    """Automatically assign Free plan to new users."""
    if created:
        # Get or create Free plan
        free_plan, _ = SubscriptionPlan.objects.get_or_create(
            tier=MembershipTier.FREE,
            defaults={
                'name': 'Free',
                'price_monthly': 0,
                'daily_quiz_limit': 5,
                'can_enter_competitions': False,
                'has_progress_tracking': False,
                'has_detailed_analytics': False,
                'has_certificates': False,
                'is_ad_free': False,
                'access_all_questions': False,
                'description': 'Perfect to get started with basic features',
            }
        )
        
        # Create subscription (indefinite for free plan)
        UserSubscription.objects.create(
            user=instance,
            plan=free_plan,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            end_date=None,  # Free plan never expires
        )
