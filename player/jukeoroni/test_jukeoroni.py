# import unittest
from django.test import TestCase
from player.jukeoroni.jukeoroni import JukeOroni


class TestJukeOroni(TestCase):
    def setUp(self):
        self.j = JukeOroni()
        # self.j.turn_on()

    def tearDown(self):
        # self.j.turn_off()
        del self.j

    def test_turn_on(self):
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
        with self.assertRaises(Exception):
            self.j.insert()

