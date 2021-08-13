# class Channel(object):
#     def __init__(self, channel):
#         self.channel = channel
#         # self.process = multiprocessing.Process(target=self.play)
#         # self.process.daemon = False
#
#     @property
#     def cover(self):
#         return self.channel.url_logo
#
#     def play(self):
#         # os.system(f'ffplay -hide_banner -autoexit -vn -nodisp -loglevel error \"{self.playing_from}\"')
#         os.system(f'mplayer -nogui -noconfig all -novideo -nocache -playlist \"{self.channel.url}\"')
