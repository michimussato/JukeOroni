from django.http import HttpResponse
from .player import player


player()


# Create your views here.
def index(request):
    return HttpResponse('Player page')
