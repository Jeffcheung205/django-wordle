from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "_dev/home.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)
