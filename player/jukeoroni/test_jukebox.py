import inspect
import logging
# import subprocess
# import sys
# import unittest
# from subprocess import Popen
import time

from django.test import TestCase
from player.jukeoroni.juke_box import Jukebox
from player.jukeoroni.settings import GLOBAL_LOGGING_LEVEL
# from player.models import Channel


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)

# ps = subprocess.Popen(['ps -o cmd -p $(pidof ffplay) | grep -i ffplay'], shell=True,
#                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# output = ps.communicate()[0].decode('utf-8').replace('\n', '')
# if output != '':
#     print('FFPLAY IS PLAYING! CANNOT TEST, AUDIO HARDWARE BUSY!!!')
#     sys.exit(1)


class TestJukebox(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestJukebox, cls).setUpClass()

    def setUp(self):
        self.box = Jukebox()

    def tearDown(self):
        try:
            self.box.turn_off()
        except:
            pass

    def test_turn_on(self):
        LOG.info(f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')

        self.assertFalse(self.box.on)
        self.box.turn_on()
        self.assertTrue(self.box.on)

        with self.assertRaises(AssertionError):
            self.box.turn_on()

    def test_turn_off(self):
        LOG.info(
            f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')

        self.assertFalse(self.box.on)
        self.box.turn_on()

        self.box.turn_off()
        with self.assertRaises(AssertionError):
            self.box.turn_off()

        self.assertFalse(self.box.on)

    def test_track_list_generator_thread(self):
        LOG.info(
            f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')

        with self.assertRaises(AssertionError):
            self.box.track_list_generator_thread()

        self.box.turn_on()

        with self.assertRaises(AssertionError):
            self.box.track_list_generator_thread()

        for i in range(5):
            LOG.info('waiting...')
            time.sleep(1.0)

        self.assertFalse(self.box._auto_update_tracklist)

        # start tracklist generator and enable auto updater
        self.box.set_auto_update_tracklist_on()

        for i in range(5):
            LOG.info('waiting...')
            time.sleep(1.0)

        self.assertIsNotNone(self.box._track_list_generator_thread)
        self.assertTrue(self.box._auto_update_tracklist)

        # keep active process running but disable auto updater
        self.box.set_auto_update_tracklist_off()

        for i in range(5):
            LOG.info('waiting...')
            time.sleep(1.0)

        self.assertFalse(self.box._auto_update_tracklist)
        self.assertIsNotNone(self.box._track_list_generator_thread)

        # stop process entirely to shutdown jukebox
        LOG.info('trying to stop track list updater thread...')
        self.box.turn_off()
        self.assertFalse(self.box.on)

        for i in range(5):
            LOG.info('waiting...')
            time.sleep(1.0)

        self.assertIsNone(self.box._track_list_generator_thread)

    def test_track_list_generator_thread_on_off(self):
        LOG.info(
            f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')

        self.box.set_auto_update_tracklist_on()

        self.assertIsNone(self.box._track_list_generator_thread)

        self.box.turn_on()

        for i in range(5):
            LOG.info('waiting...')
            time.sleep(1.0)

        self.assertIsNotNone(self.box._track_list_generator_thread)

        self.box.turn_off()

        for i in range(5):
            LOG.info('waiting...')
            time.sleep(1.0)

        self.assertIsNone(self.box._track_list_generator_thread)

        # make sure the thread is not hanging here


