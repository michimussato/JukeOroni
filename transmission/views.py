from django.http import HttpResponseRedirect
# from django.shortcuts import render

# Create your views here.


def index(request):
    return HttpResponseRedirect('http://127.0.0.1:9091/transmission/web/')
