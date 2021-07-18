from django.http import HttpResponse, HttpResponseRedirect
import subprocess

from .models import Channel

import os


# Create your views here.
def index(request):
    channels = Channel.objects.all()

    ret = '<body>\n'
    ret += '  <html>\n'
    for channel in channels:
        if channel.is_enabled:
            # required to find out if and which channel is playing
            ps = subprocess.Popen(['ps -o cmd -p $(pidof mplayer) | grep -i {0}'.format(channel.url)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = ps.communicate()[0].decode('utf-8').replace('\n', '')
            if output != '':
                pid = subprocess.Popen(['pidof mplayer'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                pid_output = pid.communicate()[0].decode('utf-8').replace('\n', '')
                ret += '        <button style=\"width:100%; background-color:green; \" onclick=\"window.location.href = \'stop/{0}\';\">{1}</button>\n'.format(pid_output, channel.display_name)  # , channel.display_name)
            else:
                ret += '        <button style=\"width:100%\" onclick=\"window.location.href = \'{0}/play\';\">{1}</button>\n'.format(channel.display_name_short, channel.display_name)
    ret += '  </html>\n'
    ret += '</body>\n'
    return HttpResponse(ret)


def play(request, display_name_short):

    pid = subprocess.Popen(['pidof mplayer'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pid_output = pid.communicate()[0].decode('utf-8').replace('\n', '')

    if pid_output != '':
        os.system('kill {0}'.format(pid_output))
    # channels = Channel.objects.all()
    subprocess.Popen(['mplayer', '-nogui', '-noconfig', 'all', '-novideo', '-nocache', '-playlist', Channel.objects.get(display_name_short=display_name_short).url])

    return HttpResponseRedirect('/radio')


def stop(request, pid):
    os.system('kill {0}'.format(pid))
    return HttpResponseRedirect('/radio')

