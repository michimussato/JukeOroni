import inspect
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
        # self.j.turn_on()

    def tearDown(self):
        # self.j.turn_off()
        del self.j

    def test_turn_on(self):
        print(inspect.getframeinfo(inspect.currentframe()).function)
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

    def test_turn_off(self):
        print(inspect.getframeinfo(inspect.currentframe()).function)
        self.j.turn_on()

        self.assertTrue(self.j.on)
        self.assertTrue(self.j._pimoroni_watcher_thread.is_alive())
        self.assertTrue(self.j._state_watcher_thread.is_alive())
        self.assertTrue(self.j.layout_standby.radar.on)
        self.assertIsNotNone(self.j.layout_standby.radar.radar_thread)
        self.assertTrue(self.j.layout_standby.radar.radar_thread.is_alive())

        self.j.turn_off()

        self.assertFalse(self.j.on)
        self.assertFalse(self.j._pimoroni_watcher_thread.is_alive())
        self.assertFalse(self.j._state_watcher_thread.is_alive())
        self.assertFalse(self.j.layout_standby.radar.on)
        self.assertIsNone(self.j.layout_standby.radar.radar_thread)
        # self.assertFalse(self.j.layout_standby.radar.radar_thread.is_alive())

    def test_insert(self):
        print(inspect.getframeinfo(inspect.currentframe()).function)

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
