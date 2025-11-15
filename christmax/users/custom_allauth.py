# though different parts of cutomization should be put in different files
# make things start here first

from allauth.account.adapter import DefaultAccountAdapter

class MyAccountAdapter(DefaultAccountAdapter):

    # this is overriding, better lookup the super class implmentation first
    def get_login_redirect_url(self, request):
        # path = "/accounts/{username}/"
        # return path.format(username=request.user.username)
        print('hihi')
        return '/accounts/email/'
