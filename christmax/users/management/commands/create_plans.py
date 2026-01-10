"""
Management command to create default subscription plans.
"""
from django.core.management.base import BaseCommand
from users.models import SubscriptionPlan, MembershipTier


class Command(BaseCommand):
    help = 'Create default subscription plans (Free and Premium)'

    def handle(self, *args, **options):
        # Create Free Plan
        free_plan, created = SubscriptionPlan.objects.update_or_create(
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
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created Free plan'))
        else:
            self.stdout.write(self.style.WARNING(f'Updated Free plan'))
        
        # Create Premium Plan
        premium_plan, created = SubscriptionPlan.objects.update_or_create(
            tier=MembershipTier.PREMIUM,
            defaults={
                'name': 'Premium',
                'price_monthly': 20,
                'daily_quiz_limit': 0,  # Unlimited
                'can_enter_competitions': True,
                'has_progress_tracking': True,
                'has_detailed_analytics': True,
                'has_certificates': True,
                'is_ad_free': True,
                'access_all_questions': True,
                'description': 'For serious learners who want unlimited access',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created Premium plan (HK$20/month)'))
        else:
            self.stdout.write(self.style.WARNING(f'Updated Premium plan (HK$20/month)'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Subscription plans ready!'))
