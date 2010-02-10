from django.conf import settings
from secret.models import Secret
from discussion.models import Discussion
from utils.shortcuts import context_response


def home(request):
    "Landing page to site. Much more to come..."
    # TODO: everything
    context = {
        'secrets': Secret.viewable.all().order_by('-created_at'),
        'discussions': Discussion.viewable.all().order_by('-created_at'),
        'facebook_key': settings.FACEBOOK_API_KEY,
    }
    return context_response(request, 'utils/home.html', context)
