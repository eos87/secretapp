from utils.shortcuts import context_response

def home(request):
    "Landing page to site. Much more to come..."
    # TODO: everything
    context = {}
    return context_response(request, 'utils/home.html', context)