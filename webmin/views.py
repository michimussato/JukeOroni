import platform
import socket

from django.http import HttpResponseRedirect
# from django.shortcuts import render

# Create your views here.


def index(request):
    # host info
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # android uses ipv6; pure hostname redirection fails, hence ipv4
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError:
        ip = platform.node()
    finally:
        s.close()
    return HttpResponseRedirect('https://{hostname}:10000'.format(hostname=ip))
