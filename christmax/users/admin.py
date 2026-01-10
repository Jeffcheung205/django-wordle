from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count, Q
from django.utils import timezone

from .models import Profile, User, SubscriptionPlan, UserSubscription


class ProfileInline(admin.StackedInline):
    """Inline admin for Profile - shows profile inside User admin."""

    model = Profile
    can_delete = False
    verbose_name_plural = _('Profile')
    fk_name = 'user'

    fields = ('display_name', 'player_level', 'experience_points', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin - extends Django's UserAdmin.

    Uses username for Django admin login (standard approach).
    """

    # What to display in the user list
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    # Show profile inline when editing a user
    inlines = (ProfileInline,)

    # Fields to show when viewing/editing a user
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (
            _('Permissions'),
            {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')},
        ),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Fields to show when creating a new user
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('username', 'email', 'password1', 'password2')}),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin interface for Profile - standalone view."""

    list_display = ('user', 'display_name', 'player_level', 'experience_points', 'created_at')
    list_filter = ('player_level', 'created_at')
    search_fields = ('user__username', 'user__email', 'display_name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Profile Info'), {'fields': ('display_name', 'player_level', 'experience_points')}),
        (_('Metadata'), {'fields': ('created_at', 'updated_at')}),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make user field read-only when editing existing profile."""
        if obj:  # Editing existing profile
            return list(self.readonly_fields) + ['user']
        return self.readonly_fields


class UserSubscriptionInline(admin.TabularInline):
    """Inline admin for UserSubscription - shows subscriptions inside User admin."""
    
    model = UserSubscription
    extra = 0
    fields = ('plan', 'status', 'start_date', 'end_date', 'auto_renew', 'payment_method')
    readonly_fields = ('start_date',)
    can_delete = False


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Admin interface for managing subscription plans."""
    
    list_display = (
        'name', 'tier', 'price_display', 'daily_quiz_limit',
        'subscriber_count', 'is_active', 'created_at'
    )
    list_filter = ('tier', 'is_active', 'can_enter_competitions', 'has_progress_tracking')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'subscriber_count', 'active_subscriber_count')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'tier', 'price_monthly', 'description', 'is_active')
        }),
        (_('Feature Limits'), {
            'fields': (
                'daily_quiz_limit',
                'access_all_questions',
                'can_enter_competitions',
            )
        }),
        (_('Premium Features'), {
            'fields': (
                'has_progress_tracking',
                'has_detailed_analytics',
                'has_certificates',
                'is_ad_free',
            )
        }),
        (_('Statistics'), {
            'fields': ('subscriber_count', 'active_subscriber_count'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def price_display(self, obj):
        """Display price with currency."""
        if obj.price_monthly == 0:
            return format_html('<span style="color: green; font-weight: bold;">FREE</span>')
        return format_html(
            '<span style="color: #007bff; font-weight: bold;">HK${}</span>',
            obj.price_monthly
        )
    price_display.short_description = _('Price')
    
    def subscriber_count(self, obj):
        """Total number of subscribers (all time)."""
        return obj.subscriptions.count()
    subscriber_count.short_description = _('Total Subscribers')
    
    def active_subscriber_count(self, obj):
        """Number of currently active subscribers."""
        count = obj.subscriptions.filter(status='ACTIVE').count()
        return format_html(
            '<span style="color: green; font-weight: bold;">{}</span>',
            count
        )
    active_subscriber_count.short_description = _('Active Subscribers')


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for managing user subscriptions."""
    
    list_display = (
        'user_email', 'plan', 'status_badge', 'start_date',
        'end_date', 'days_remaining_display', 'auto_renew', 'payment_method'
    )
    list_filter = (
        'status', 'plan', 'auto_renew', 'payment_method',
        'start_date', 'end_date'
    )
    search_fields = ('user__email', 'user__username', 'transaction_id', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'days_remaining_display')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (_('Subscription Details'), {
            'fields': ('user', 'plan', 'status')
        }),
        (_('Period'), {
            'fields': ('start_date', 'end_date', 'days_remaining_display', 'cancelled_at')
        }),
        (_('Payment Information'), {
            'fields': ('payment_method', 'transaction_id', 'auto_renew')
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_subscriptions', 'cancel_subscriptions', 'mark_expired']
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = _('User')
    user_email.admin_order_field = 'user__email'
    
    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'ACTIVE': '#28a745',
            'EXPIRED': '#6c757d',
            'CANCELLED': '#dc3545',
            'TRIAL': '#17a2b8',
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'
    
    def days_remaining_display(self, obj):
        """Display days remaining in subscription."""
        if not obj.end_date:
            return format_html('<span style="color: green;">∞ Indefinite</span>')
        
        days = obj.days_remaining()
        if days == 0:
            return format_html('<span style="color: red; font-weight: bold;">Expired</span>')
        elif days <= 7:
            return format_html('<span style="color: orange; font-weight: bold;">{} days</span>', days)
        else:
            return format_html('<span style="color: green;">{} days</span>', days)
    days_remaining_display.short_description = _('Days Remaining')
    
    def activate_subscriptions(self, request, queryset):
        """Bulk action to activate subscriptions."""
        updated = queryset.update(status='ACTIVE')
        self.message_user(request, f'{updated} subscription(s) activated.')
    activate_subscriptions.short_description = _('Activate selected subscriptions')
    
    def cancel_subscriptions(self, request, queryset):
        """Bulk action to cancel subscriptions."""
        count = 0
        for subscription in queryset:
            subscription.cancel()
            count += 1
        self.message_user(request, f'{count} subscription(s) cancelled.')
    cancel_subscriptions.short_description = _('Cancel selected subscriptions')
    
    def mark_expired(self, request, queryset):
        """Bulk action to mark subscriptions as expired."""
        updated = queryset.update(status='EXPIRED')
        self.message_user(request, f'{updated} subscription(s) marked as expired.')
    mark_expired.short_description = _('Mark selected subscriptions as expired')
