import inspect
import logging
import subprocess
import sys
import unittest
from subprocess import Popen
from django.test import TestCase
from player.jukeoroni.jukeoroni import JukeOroni
from player.jukeoroni.settings import Settings
from player.models import Channel


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)

ps = subprocess.Popen(['ps -o cmd -p $(pidof ffplay) | grep -i ffplay'], shell=True,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output = ps.communicate()[0].decode('utf-8').replace('\n', '')
if output != '':
    print('FFPLAY IS PLAYING! CANNOT TEST, AUDIO HARDWARE BUSY!!!')
    sys.exit(1)


class TestJukeOroni(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestJukeOroni, cls).setUpClass()

        _fixture_channel_list = [
            ("BOBs 100", "100", True, "http://bob.hoerradar.de/radiobob-100-mp3-hq", None, False),
            ("BOBs 101", "101", True, "http://bob.hoerradar.de/radiobob-101-mp3-hq", None, False),
            ("BOBs Festival", "bob-festival", True, "http://bob.hoerradar.de/radiobob-festival-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_festival_600x600.png", False),
            ("BOBs Harte Saite", "bob-hartesaite", True, "http://bob.hoerradar.de/radiobob-hartesaite-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_harte-saite_600x600.png", True),
            ("BOBs 2000er", "2000er", True, "http://bob.hoerradar.de/radiobob-2000er-mp3-hq",
             "http://aggregatorservice.loverad.io/wp-content/uploads/2021/03/bob_2000er-rock_600x600.png", False),
        ]

        for channel in _fixture_channel_list:
            c = Channel(display_name=channel[0], display_name_short=channel[1], is_enabled=channel[2], url=channel[3],
                        url_logo=channel[4])
            c.save()

    def setUp(self):
        self.j = JukeOroni()
        self.j.test = True

    def tearDown(self):
        # try/except is only here to make sure
        # that the tests don't hang if turn_off()
        # procedure cannot be executed for some
        # reason. In that case, the
        # j._buttons_watcher_thread will hang
        # and the test won't finish.
        try:
            self.j.stop()
        except:
            pass
        try:
            self.j.eject()
        except:
            pass
        try:
            self.j.turn_off()
        except:
            pass

    def test_turn_on(self):
        LOG.info(f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')
        self.assertFalse(self.j.on)
        self.assertIsNone(self.j._state_watcher_thread)
        self.assertIsNone(self.j._pimoroni_watcher_thread)
        self.assertFalse(self.j.layout_standby.radar.on)
        self.assertIsNone(self.j.layout_standby.radar.radar_thread)

        self.j.turn_on()

        self.assertTrue(self.j.on)
        # self.assertIsNotNone(self.j._state_watcher_thread)
        self.assertIsNotNone(self.j._pimoroni_watcher_thread)
        # self.assertTrue(self.j._state_watcher_thread.is_alive())
        self.assertTrue(self.j._pimoroni_watcher_thread.is_alive())
        self.assertTrue(self.j.layout_standby.radar.on)
        self.assertIsNotNone(self.j.layout_standby.radar.radar_thread)
        self.assertTrue(self.j.layout_standby.radar.radar_thread.is_alive())

        self.j.turn_off()

    def test_turn_off(self):
        LOG.info(f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')

        self.j.turn_on()

        self.assertTrue(self.j.on)
        self.assertTrue(self.j._pimoroni_watcher_thread.is_alive())
        # self.assertTrue(self.j._state_watcher_thread.is_alive())
        self.assertTrue(self.j.layout_standby.radar.on)
        self.assertIsNotNone(self.j.layout_standby.radar.radar_thread)
        self.assertTrue(self.j.layout_standby.radar.radar_thread.is_alive())

        self.j.turn_off()

        self.assertFalse(self.j.on)
        self.assertIsNone(self.j._pimoroni_watcher_thread)
        self.assertIsNone(self.j._state_watcher_thread)
        self.assertFalse(self.j.layout_standby.radar.on)
        self.assertIsNone(self.j.layout_standby.radar.radar_thread)

    def test_insert(self):
        LOG.info(f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')

        self.j.turn_on()

        with self.assertRaises(Exception):
            self.j.insert()

        with self.assertRaises(AssertionError):
            self.j.play()
            self.j.pause()
            self.j.resume()
            self.j.stop()
            self.j.eject()

        # with self.assertRaises(AssertionError):
        #     self.j.next()

        with self.assertRaises(NotImplementedError):
            self.j.previous()

        self.assertIsNone(self.j.inserted_media)
        media1 = Channel.objects.all()[0]
        self.j.insert(media=media1)
        self.assertIsNotNone(self.j.inserted_media)
        self.assertEquals('http://bob.hoerradar.de/radiobob-100-mp3-hq',
                          self.j.inserted_media.url)

        media2 = Channel.objects.all()[1]
        with self.assertRaises(AssertionError):
            self.j.insert(media=media2)

        self.j.eject()

        self.j.turn_off()

    def test_last_played(self):
        self.assertIsNone(self.j.radio.last_played)

        self.j.turn_on()

        media1 = Channel.objects.all()[2]
        media2 = Channel.objects.all()[3]
        self.j.insert(media=media1)

        self.assertIsNone(self.j.radio.last_played)

        self.j.play()
        
        self.assertIsNotNone(self.j.radio.last_played)
        
        self.assertEqual(self.j.radio.last_played, media1)
        self.assertNotEqual(self.j.radio.last_played, media2)

        self.j.stop()
        self.j.eject()

        self.j.insert(self.j.radio.last_played)
        self.j.change_media(media=media2)
        self.assertEqual(self.j.radio.last_played, media1)
        self.j.play()
        self.assertEqual(self.j.radio.last_played, media2)
        self.assertEqual(self.j.radio.last_played.display_name_short, media2.display_name_short)

        self.j.stop()
        self.j.eject()
        self.j.turn_off()

    def test_play(self):
        LOG.info(f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')

        self.j.turn_on()

        with self.assertRaises(Exception):
            self.j.play()

        with self.assertRaises(Exception):
            self.j.insert(media='Medium')

        media = Channel.objects.all()[2]
        self.j.insert(media=media)

        self.assertIsNone(self.j.radio.is_on_air)
        self.assertIsNone(self.j.playback_proc)
        self.j.play()
        self.assertIsInstance(self.j.radio.is_on_air, Channel)
        self.assertIsInstance(self.j.playback_proc, Popen)
        self.assertIsNone(self.j.playback_proc.poll())

        # media = Channel.objects.all()[0]
        # self.j.insert(media=media)

        with self.assertRaises(Exception):
            self.j.play()

        self.j.stop()
        self.j.eject()

        media = Channel.objects.all()[4]
        self.j.insert(media=media)
        import urllib.error
        with self.assertRaises(urllib.error.HTTPError):
            self.j.play()
        with self.assertRaises(AssertionError):
            self.j.turn_off()

        self.j.eject()

        self.j.turn_off()

    def test_next(self):
        LOG.info(
            f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')

        self.j.turn_on()

        media1 = Channel.objects.all()[2]
        self.j.insert(media=media1)

        with self.assertRaises(AssertionError):
            self.j.next()

        media2 = Channel.objects.all()[3]
        self.j.play()
        self.j.next(media=media2)

        self.assertTrue(self.j.inserted_media is media2)
        self.assertIsNotNone(self.j.playback_proc)

        self.j.stop()
        self.j.eject()
        self.j.turn_off()

    @unittest.skip
    def test_pause(self):
        LOG.info(f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')
        raise NotImplementedError

    @unittest.skip
    def test_resume(self):
        LOG.info(f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')
        raise NotImplementedError

    def test_stop(self):
        LOG.info(f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')

        self.j.turn_on()

        with self.assertRaises(AssertionError):
            self.j.stop()

        media = Channel.objects.all()[0]
        self.j.insert(media=media)

        with self.assertRaises(AssertionError):
            self.j.stop()

        self.j.play()

        self.assertIsInstance(self.j.radio.is_on_air, Channel)
        self.assertIsInstance(self.j.playback_proc, Popen)
        self.assertIsNone(self.j.playback_proc.poll())

        self.j.stop()

        self.assertIsNone(self.j.radio.is_on_air)
        self.assertIsNone(self.j.playback_proc)

        self.j.eject()
        self.j.turn_off()

    @unittest.skip
    def test_previous(self):
        LOG.info(f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')
        raise NotImplementedError

    def test_eject(self):
        LOG.info(f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')

        self.j.turn_on()

        with self.assertRaises(AssertionError):
            self.j.eject()

        media = Channel.objects.all()[2]
        self.j.insert(media=media)

        self.assertIs(media, self.j.inserted_media)
        self.assertIsNone(self.j.playback_proc)

        self.j.eject()

        self.assertIsNone(self.j.inserted_media)
        self.assertIsNone(self.j.playback_proc)

        self.j.insert(media=media)
        self.j.play()

        self.assertIsInstance(self.j.playback_proc, Popen)

        with self.assertRaises(AssertionError):
            self.j.eject()

        self.j.stop()
        self.assertIs(media, self.j.inserted_media)
        self.assertIsNone(self.j.playback_proc)
        self.j.eject()
        self.assertIsNone(self.j.inserted_media)

        self.j.turn_off()

    def test_change_media(self):
        LOG.info(f'\n############################\nRunning test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')

        self.j.turn_on()

        media_1 = Channel.objects.all()[0]
        media_2 = Channel.objects.all()[1]

        # while not playing
        self.j.insert(media=media_1)
        self.assertIsNone(self.j.radio.is_on_air)
        self.assertEqual(self.j.inserted_media, media_1)
        self.j.change_media(media=media_2)
        self.assertIsNone(self.j.radio.is_on_air)

        self.assertEqual(self.j.inserted_media, media_2)

        self.j.eject()

        # while playing
        self.j.insert(media=media_1)
        self.j.play()
        self.assertIsInstance(self.j.radio.is_on_air, Channel)
        self.assertEqual(self.j.inserted_media, media_1)
        with self.assertRaises(AssertionError):
            self.j.change_media(media=media_2)
        self.j.stop()
        self.j.change_media(media=media_2)
        self.j.play()
        self.assertIsInstance(self.j.radio.is_on_air, Channel)
        self.assertEqual(self.j.inserted_media, media_2)

        self.j.stop()
        self.j.eject()
        self.j.turn_off()
