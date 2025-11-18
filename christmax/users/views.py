from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator


@method_decorator(login_required, name='dispatch')
class SettingsView(TemplateView):
    """Settings dashboard/overview page showing account status."""
    template_name = 'account/settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Check email verification status
        context['email_verified'] = user.emailaddress_set.filter(verified=True).exists()
        
        # Check if user has a password set (vs only social login)
        context['has_password'] = user.has_usable_password()
        
        # Get connected social accounts
        context['social_accounts'] = user.socialaccount_set.all()
        
        return context
