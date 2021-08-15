import inspect
from subprocess import Popen
from django.test import TestCase
from player.jukeoroni.jukeoroni import JukeOroni
from player.models import Channel


class TestJukeOroni(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestJukeOroni, cls).setUpClass()

        channel_list = [
            ("BOBs 100", "100", True, "http://bob.hoerradar.de/radiobob-100-mp3-hq", None, False),
            ("BOBs 101", "101", True, "http://bob.hoerradar.de/radiobob-101-mp3-hq", None, False),
            ("BOBs 2000er", "2000er", True, "http://bob.hoerradar.de/radiobob-2000er-mp3-hq",
             "http://aggregatorservice.loverad.io/wp-content/uploads/2021/03/bob_2000er-rock_600x600.png", False),
            ("BOBs Blues", "blues", True, "http://bob.hoerradar.de/radiobob-blues-mp3-hq",
             "http://aggregatorservice.loverad.io/wp-content/uploads/2021/03/bob_2000er-rock_600x600.png", False),
        ]

        for channel in channel_list:
            c = Channel(display_name=channel[0], display_name_short=channel[1], is_enabled=channel[2], url=channel[3],
                        url_logo=channel[4])
            c.save()

    def setUp(self):
        self.j = JukeOroni()
        self.j.test = True

    def tearDown(self):
        del self.j

    def test_turn_on(self):
        print('\n\n############################')
        print(f'Running test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')
        self.assertFalse(self.j.on)
        self.assertIsNone(self.j._state_watcher_thread)
        self.assertIsNone(self.j._pimoroni_watcher_thread)
        self.assertFalse(self.j.layout_standby.radar.on)
        self.assertIsNone(self.j.layout_standby.radar.radar_thread)

        self.j.turn_on()

        self.assertTrue(self.j.on)
        self.assertIsNotNone(self.j._state_watcher_thread)
        self.assertIsNotNone(self.j._pimoroni_watcher_thread)
        self.assertTrue(self.j._state_watcher_thread.is_alive())
        self.assertTrue(self.j._pimoroni_watcher_thread.is_alive())
        self.assertTrue(self.j.layout_standby.radar.on)
        self.assertIsNotNone(self.j.layout_standby.radar.radar_thread)
        self.assertTrue(self.j.layout_standby.radar.radar_thread.is_alive())

        self.j.turn_off()

    def test_turn_off(self):
        print('\n\n############################')
        print(f'Running test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')
        self.j.turn_on()

        self.assertTrue(self.j.on)
        self.assertTrue(self.j._pimoroni_watcher_thread.is_alive())
        self.assertTrue(self.j._state_watcher_thread.is_alive())
        self.assertTrue(self.j.layout_standby.radar.on)
        self.assertIsNotNone(self.j.layout_standby.radar.radar_thread)
        self.assertTrue(self.j.layout_standby.radar.radar_thread.is_alive())

        self.j.turn_off()

        self.assertFalse(self.j.on)
        self.assertIsNone(self.j._pimoroni_watcher_thread)
        self.assertIsNone(self.j._state_watcher_thread)
        self.assertFalse(self.j.layout_standby.radar.on)
        self.assertIsNone(self.j.layout_standby.radar.radar_thread)
        # self.assertFalse(self.j.layout_standby.radar.radar_thread.is_alive())

    def test_insert(self):
        print('\n\n############################')
        print(f'Running test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')

        with self.assertRaises(Exception):
            self.j.insert()

        with self.assertRaises(AssertionError):
            self.j.play()
            self.j.pause()
            self.j.resume()
            self.j.stop()
            self.j.eject()

        with self.assertRaises(NotImplementedError):
            self.j.next()
            self.j.previous()

        self.assertIsNone(self.j.inserted_media)
        media = Channel.objects.all()[0]
        self.j.insert(media=media)
        self.assertIsNotNone(self.j.inserted_media)
        self.assertEquals('http://bob.hoerradar.de/radiobob-100-mp3-hq',
                          self.j.inserted_media.url)

    def test_play(self):
        print('\n\n############################')
        print(f'Running test: {str(inspect.getframeinfo(inspect.currentframe()).function)}\n')

        with self.assertRaises(Exception):
            self.j.play()

        with self.assertRaises(Exception):
            self.j.insert(media='Medium')

        media = Channel.objects.all()[0]
        self.j.insert(media=media)

        self.assertFalse(self.j.radio.is_on_air)
        self.assertIsNone(self.j.playback_proc)
        self.j.play()
        self.assertTrue(self.j.radio.is_on_air)
        self.assertIsInstance(self.j.playback_proc, Popen)
        self.assertIsNone(self.j.playback_proc.poll())

    def test_pause(self):
        pass

    def test_resume(self):
        pass

    def test_stop(self):

        with self.assertRaises(AssertionError):
            self.j.stop()

        media = Channel.objects.all()[0]
        self.j.insert(media=media)

        with self.assertRaises(AssertionError):
            self.j.stop()

        self.j.play()

        self.assertTrue(self.j.radio.is_on_air)
        self.assertIsInstance(self.j.playback_proc, Popen)
        self.assertIsNone(self.j.playback_proc.poll())

        self.j.stop()

        self.assertFalse(self.j.radio.is_on_air)
        self.assertIsNone(self.j.playback_proc)

    def test_next(self):
        pass

    def test_previous(self):
        pass

    def test_eject(self):
        with self.assertRaises(AssertionError):
            self.j.eject()

        # self.assertIsNone(self.j.inserted_media)
        # self.assertIsNone(self.j.playback_proc)

        media = Channel.objects.all()[0]
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


