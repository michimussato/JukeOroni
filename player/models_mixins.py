from pathlib import Path
import threading
from omxplayer.player import OMXPlayer

from django.db import models
from jukeoroni.settings import Settings


# Abstract classes here
class JukeOroniMediumAbstract(models.Model):

    class Meta:
        abstract = True

    def play(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    @property
    def source_file(self):
        raise NotImplementedError()


# class VideoMixin(JukeOroniMediumAbstract):
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.omxplayer = None
#         self._start_paused = False
#
#     def play(self):
#         self._omxplayer_thread = threading.Thread(target=self._play)
#         self._omxplayer_thread.name = f'OMXPlayer Playback Thread ({self.video_title})'
#         self._omxplayer_thread.daemon = False
#         self._omxplayer_thread.start()
#
#     def _play(self):
#         self.omxplayer = OMXPlayer(
#             self.source_file.as_posix(),
#             args=['--no-keys', '--adev', Settings.AUDIO_OUT],
#             # dbus_name='org.mpris.MediaPlayer2.omxplayer1',
#             pause=self._start_paused,
#         )
#
#     def stop(self):
#         """Stop the playback; will quit the Player"""
#         if isinstance(self.omxplayer, OMXPlayer):
#             if self.omxplayer.is_playing():
#                 self.omxplayer.stop()
#                 self.omxplayer = None
#
#     def play_pause(self):
#         if isinstance(self.omxplayer, OMXPlayer):
#             self.omxplayer.play_pause()
#
#     @property
#     def source_file(self):
#         return Path(Settings.VIDEO_DIR) / self.video_source
