"""
subprocess
The subprocess module lets you run and control other programs. Anything you can start with the command line on the computer, can be run and controlled with this module. Use this to integrate external programs into your Python code.

multiprocessing
The multiprocessing module lets you divide tasks written in python over multiple processes to help improve performance. It provides an API very similar to the threading module; it provides methods to share data across the processes it creates, and makes the task of managing multiple processes to run Python code (much) easier. In other words, multiprocessing lets you take advantage of multiple processes to get your tasks done faster by executing code in parallel.
(can run on several cores)

threading
The threading module uses threads, the multiprocessing module uses processes. The difference is that threads run in the same memory space, while processes have separate memory. This makes it a bit harder to share objects between processes with multiprocessing. Since threads use the same memory, precautions have to be taken or two threads will write to the same memory at the same time. This is what the global interpreter lock is for.
(no multicore usage, but process concurrency/context switching)
"""


"""
event based start/suspend/resume thread

import threading
import time

# This function gets called by our thread.. so it basically becomes the thread innit..                    
def wait_for_event(e):
    while True:
        print '\tTHREAD: This is the thread speaking, we are Waiting for event to start..'
        event_is_set = e.wait()
        print '\tTHREAD:  WHOOOOOO HOOOO WE GOT A SIGNAL  : %s', event_is_set
        e.clear()

# Main code.. 
e = threading.Event()
t = threading.Thread(name='your_mum', 
                     target=wait_for_event,
                     args=(e,))
t.start()

while True:
    print 'MAIN LOOP: still in the main loop..'
    time.sleep(4)
    print 'MAIN LOOP: I just set the flag..'
    e.set()
    print 'MAIN LOOP: now Im gonna do some processing n shi-t'
    time.sleep(4)
    print 'MAIN LOOP:  .. some more procesing im doing   yeahhhh'
    time.sleep(4)
    print 'MAIN LOOP: ok ready, soon we will repeat the loop..'
    time.sleep(2)
"""


class PlayerBase(object):
    ACCEPTED_OBJECTS = list()
    CMD = str()

    def turn_on(self):
        pass

    def shut_down(self):
        pass

    def insert(self):
        pass

    def eject(self):
        pass

    def play(self):
        pass

    def pause(self):
        pass

    def stop(self):
        pass

    def pid(self):
        pass


# class AudiobookBox(PlayerBase):
#     ACCEPTED_OBJECTS = []
#
#
# class MeditationBox(PlayerBase):
#     ACCEPTED_OBJECTS = []


# class JukeBox(PlayerBase):
#     ACCEPTED_FILES = ['.dsf', '.flac', '.wav', '.dff']
#     # Plays Tracks and Albums
#     #
#     CMD = 'ffplay -hide_banner -autoexit -nodisp -vn -loglevel quiet {file}'
#
#     def __init__(self):
#
#         self.loaded_tracks_queue = []
#
#     ############################################
#     # turn on procedure
#     def turn_on(self):
#         self.track_list_generator_thread()
#         self.track_loader_thread()
#     ############################################
#
#     def play(self):
#         pass
#
#     def pause(self):
#         pass
#
#     def stop(self):
#         pass
#
#     def next(self):
#         pass
#
#     def insert(self):
#         pass
#
#     def eject(self):
#         pass
#
#     ############################################
#     # track loader
#     def track_loader_thread(self):
#         self._track_loader_thread = threading.Thread(target=self._track_loader_task)
#         self._track_loader_thread.name = 'Track Loader Thread'
#         self._track_loader_thread.daemon = False
#         self._track_loader_thread.start()
#
#     def _track_loader_task(self):
#         while True:
#             if len(self.loaded_tracks_queue) + self.loading < MAX_CACHED_FILES and not bool(self.loading):
#                 next_track = self.get_next_track()
#                 if next_track is None:
#                     time.sleep(1.0)
#                     continue
#
#                 # # threading approach seems causing problems if we actually need to empty
#                 # # self.tracks. the thread will finish and add the cached track to self.tracks
#                 # # afterwards because we cannot kill the running thread
#                 # thread = threading.Thread(target=self._load_track_task, kwargs={'track': next_track})
#                 # # TODO: maybe this name is not ideal
#                 # thread.name = 'Track Loader Task Thread'
#                 # thread.daemon = False
#
#                 # multiprocessing approach
#                 # this approach apparently destroys the Track object that it uses to cache
#                 # data. when the Queue handles over that cached object, it seems like
#                 # it re-creates the Track object (pickle, probably) but the cached data is
#                 # gone of course because __del__ was called before that already.
#                 self.loading_process = multiprocessing.Process(target=self._load_track_task, kwargs={'track': next_track})
#                 self.loading_process.start()
#
#                 self.loading += 1
#
#                 # print(type(self.loading_process))
#                 # print(dir(self.loading_process))
#
#                 try:
#                     while self.loading_process.is_alive():
#                         # logging.error(self.loading_process)
#                         # print(self.loading_process)
#                         time.sleep(1.0)
#
#                     ret = self.loading_queue.get()
#
#                     if ret is not None:
#                         self.loaded_tracks_queue.append(ret)
#
#                     # logging.error(self.loading_process)
#                     self.loading_process.join()
#
#                 except AttributeError as err:
#                     print(err)
#                     logging.exception(err)
#
#                 finally:
#                     self.loading -= 1
#
#             time.sleep(1.0)
#
#     def _load_track_task(self, **kwargs):
#         track = kwargs['track']
#         logging.debug(f'starting thread: \"{track.audio_source}\"')
#         print(f'starting thread: \"{track.audio_source}\"')
#
#         try:
#             size = os.path.getsize(track.audio_source)
#             logging.info(f'loading track ({str(round(size / (1024*1024), 3))} MB): \"{track.audio_source}\"')
#             print(f'loading track ({str(round(size / (1024*1024), 3))} MB): \"{track.audio_source}\"')
#             processing_track = Track(track)
#             logging.info(f'loading successful: \"{track.audio_source}\"')
#             print(f'loading successful: \"{track.audio_source}\"')
#             ret = processing_track
#         except MemoryError as err:
#             print(err)
#             logging.exception(f'loading failed: \"{track.audio_source}\"')
#             print(f'loading failed: \"{track.audio_source}\"')
#             ret = None
#
#         # here, or after that, probably processing_track.__del__() is called but pickled/recreated
#         # in the main process
#         self.loading_queue.put(ret)
#     ############################################


# class Radio(object):
#     # Plays online radio streams (Channels)
#     # CMD = 'mplayer -nogui -noconfig all -novideo -nocache -playlist {url}'  # plays m3u
#     CMD = 'ffplay -hide_banner -autoexit -nodisp -vn -loglevel quiet {url}'  # plays the actual icy stream
#     # Header: curl --head {url}
#
#     def __init__(self):
#         self.is_playing = False
