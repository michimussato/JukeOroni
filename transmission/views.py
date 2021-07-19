import platform
from django.http import HttpResponseRedirect
# from django.shortcuts import render

# Create your views here.


def index(request):
    return HttpResponseRedirect('http://{hostname}:9091/transmission/web/'.format(hostname=platform.node()))
